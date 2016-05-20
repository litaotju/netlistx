# -*-coding:utf-8 -*- #
import os
import socket
import subprocess

import networkx as nx

import netlistx.circuit as cc
from netlistx.log import logger
from netlistx.file_util import StdOutRedirect
from netlistx.prototype.unbpath import unbalance_paths

def get_namegraph(graph):
    u'''
        @brief:
            复制原图的拓扑结构，生成一个字符串为节点的图，每一个节点的字符串对应着原图的节点名
        @param:
            graph, a graph whose node is either a cc.port() or an obj with a name attr
        return:
            返回和同等拓扑结构的图. 新图的节点是原图的节点的名称,为字符串类型变量.
    '''
    def get_name(node):
        u'''@brief:
                return the name of a node, replace \ with a / incase the Unicode error or write_dot
            @params:
                node, circuit.Port obj or circuit.Module obj
            @return:
                name, a str, Port.assgin.string or Module.name, and replace / with \
        '''
        name = ''
        if cc.isPort(node):
            name = node.port_assign.string
        else:
            #isinstance(node, cc.circuit_module)
            name = node.name
        name = name.replace('\\', '/')
        return name
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
    #x2entity = {x: entity for entity, x in entity2x.iteritems()}
    x2entities = {}
    for entity,x in entity2x.iteritems():
        if not x2entities.has_key(x):
            x2entities[x] = []
        x2entities[x].append(entity)

    with open(solutionfile, 'r') as solution:
        for line in solution:
            if line.startswith("//"): continue
            (x, val) = tuple(line.strip().split()) 
            if int(val) == 0:
                try:
                    ret += x2entities[x]
                except KeyError:
                    #如果采取合并分组的方式，有的x可能没有对应的FD
                    pass
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
        print "%s" % obj
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
        logger.debug("Matlab excuted OK!")
        # send an i to close Matlab
        connection.send(CHAR_STOP_MATLAB)
    connection.close()
    server_socket.close()
    return

def isbalanced( graph ):
    u'''@brief:给一个图，判断图是否为平衡结构
        @params:
               graph, a networkx.DiGraph
        @return:
               true if the graph is balanced structure else false
    '''
    roots = [node for node in graph.nodes_iter() if graph.in_degree()[node]==0]
    if len(roots) < 1:
        return False
    # 广度优先搜索,访问根节点，访问根节点的下一层节点， 为每一个点定Level
    # 访问一层节点的下一层节点，直到将所有的节点访问完，跳出。
    for root in roots:
        bfs_queue = [root]
        level = {root:0 }                  #记录每一个点的LEVEL的字典，初始只记录当前root
        been_levelized = []                #已经被定级的节点
        current_level = 0                  #当前的层
        while(bfs_queue):
		    # 传进来的bfs_queque的层是已知的，
		    # 记录下它们的所有后继结点，并为他们定层次为n+1,同时放到待访问序列里面
            current_level +=1
            next_level_que = []
            for eachNode in bfs_queue:
                for eachSucc in graph.successors(eachNode):
                    if not eachSucc in next_level_que:
                        next_level_que.append(eachSucc)
                        if not level.has_key(eachSucc):
                            level[eachSucc] = current_level
                        elif level[eachSucc] ==current_level:
                            continue
                        else:
                            return False
            been_levelized += bfs_queue
            bfs_queue = next_level_que
    return True