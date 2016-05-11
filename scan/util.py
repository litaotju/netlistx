# -*-coding:utf-8 -*- #
import os
import socket
import subprocess

import networkx as nx

import netlistx.circuit as cc
from netlistx.log import logger
from netlistx.file_util import StdOutRedirect
from netlistx.prototype.unbpath import unbalance_paths

__all__ = [ 'get_namegraph', 
           'upath_cycle', 
           'gen_m_script', 
           'run_matlab', 
           'read_solution']

def get_namegraph(graph):
    u'''
        @brief:
            复制原图的拓扑结构，生成一个字符串为节点的图，每一个节点的字符串对应着原图的节点名
        @param:
            graph, a graph whose node is either a cc.port() or an obj with a name attr
        return:
            返回和同等拓扑结构的图. 新图的节点是原图的节点的名称,为字符串类型变量.
    '''
    get_name = lambda node : node.name if not cc.isPort(node) else node.port_assign.string
    tmp = {}
    for node in graph.nodes_iter():
        unique_name = get_name(node)
        assert not tmp.has_key(unique_name), \
            "Node:%s, has the same name with:%s, name:%s" % (node, tmp[node.name], unique_name )
        tmp[unique_name] = node

    namegraph = nx.DiGraph()
    namegraph.original_node = tmp
    namegraph.add_nodes_from(tmp.iterkeys())
    namegraph.add_edges_from(((get_name(edge[0]), get_name(edge[1])) for edge in graph.edges_iter()))
    logger.debug("get name graph successfully")
    return namegraph

def upath_cycle(namegraph):
    u'''@ brief: 
            找出图中所有的不平衡路径和环
        @ param: 
            namegraph, a nx.DiGraph obj
        @ return: 
            (upaths, cycles) : 图中所有的不平衡路径和环
    '''       
    upaths = unbalance_paths(namegraph)
    logger.debug("get unblance path succesefully")
    cycles = []
    for cycle in nx.simple_cycles(namegraph):
        cycles.append(cycle)
    logger.debug("get cycles succesefully")
    return upaths, cycles

def read_solution(solutionfile, entity2x):
    u'''@brief:
            读取matlab的计算结果，得到需要变为扫描的边
        @params:
            sulutionfile:  文件名，每一行的形式为  x\([\d]+\) [01]
            entity2x: 字典， { entity(任何实体): x\(\[\d]+\) }
        @return:
            list, 每一个 变量x%d==0 对应的的实体组成的队列
    '''
    ret = []
    x2entity = {x: entity for entity, x in entity2x.iteritems()}
    with open(solutionfile, 'r') as solution:
        for line in solution:
            if line.startswith("//"): continue
            (x, val) = tuple(line.strip().split()) 
            if int(val) == 0:
                ret.append(x2entity[x])
    return ret

CHAR_STOP_MATLAB = 'i'
def gen_m_script(obj, contraints, binvar_length, solution_file, port, script_file):
    u'''
        @brief: 生成matlab脚本, 保存到solution_file文件夹
        @params:
            obj: objective function, it's an expression about x
            contraints: a list of constraint(str)
            binvar_length: the number of binnary decision viriables
            solution_file: a filename, tell the matlab to export the solution to this file_util
            port: a port number, tell the matlab to listen on this port for finishing signal
            script_file: a filename, print all the matlab statement to this file_util
        @return：
            True or False, indicates the script_file was generated or not
    '''
    #如果两个约束都是空的，直接返回false
    if not contraints:
        msg = 'The constraints is empty or none'
        raise Exception, msg

    # 输出matlab脚本    
    with StdOutRedirect(script_file):
        print "x = binvar(1, %d);" % binvar_length
        print ''' ops = sdpsettings('solver','bnb','bnb.solver','fmincon','bnb.method',...
                      'breadth','bnb.gaptol',1e-8,'verbose',1,'bnb.maxiter',1000,'allownonconvex',0);
        '''
        print "obj = %s;" % obj
        print "constraints = [",
        print '\n'.join(contraints)
        print "];"
        print "solvesdp(constraints, obj, ops);"
        print "fid = fopen('%s','w');" % solution_file
        print "for i = 1:%d" % binvar_length
        print "    fprintf(fid, 'x(%d)  %d\\n', i, double(x(i)));"
        print "end"
        print "t = tcpip('localhost', %d, 'NetworkRole', 'client');" % port
        print "fopen(t)"
        print "fwrite(t, 'valid')"
        print "if (fread(t) == %d )" % ord(CHAR_STOP_MATLAB)
        print "exit();"
        print "end"
    return True

def run_matlab(script_file, port):
    u'''@brief: 启动matlab运行script_file, 并且利用socket通信获知matlab何时结束
        @params:
            script_file: an existing filename to be run by matlab
            port: a port number to listen on
        @return:
            None
    '''
    # 启动Socket服务器
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    server_socket.bind(('', port))
    server_socket.listen(1)
    opath = os.path.split(script_file)[0]
    basename = os.path.splitext(os.path.split(script_file)[1])[0]
    subprocess.Popen("matlab -nodesktop -sd  %s -r %s" % (opath, basename))
    connection = server_socket.accept()[0]
    if connection.recv(100) == "valid":
        print "Matlab excuted OK!"
        # send an i to close Matlab
        connection.send(CHAR_STOP_MATLAB)
    connection.close()
    server_socket.close()
    return