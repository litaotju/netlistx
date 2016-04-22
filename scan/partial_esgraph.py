# -*- coding: utf-8 -*-
u'''直接运行本模块，输入一个路径，对该路径下的所有vm文件，提取其增广S图，然后生成matlab脚本。
   和部分扫描优化问题。
'''
import os
import socket
import sys

from netlistx.file_util import StdOutRedirect, vm_files2
from netlistx.graph.circuitgraph import get_graph
from netlistx.graph.esgraph import ESGraph
from netlistx.scan.util import get_namegraph, upath_cycle, read_solution


def get_scan_fds(esgrh, opath):
    u'''
        @brief：输入一个ESGraph对象 esgrh，和一个路径，在该路径下生成此esgrh的优化问题matlab脚本并求解。
        @params:
            esgrh: an ESGraph obj
            opath: an existing path to store the inter temp file
        @return:
            scan_fds [], a list of scan fds in esgrh
    '''
    assert isinstance(esgrh, ESGraph)
    script_file = os.path.join(opath, esgrh.name + ".m")
    solution_file = esgrh.name + "_ESGraph_ScanFDs.txt"
    port = 12345 #Socket port for matlab

    namegraph = get_namegraph(esgrh)          #namegraph = nx.DiGraph()
    selfloop_nodes = [node for node in namegraph.nodes_iter() if namegraph.has_edge(node, node)]
    namegraph.remove_nodes_from(selfloop_nodes)

    unpaths, cycles = upath_cycle(namegraph)  #unpaths = [], cycles = []

    # {name: x%d}
    node2x = {node: "x(%d)"%index for index, node in enumerate(namegraph.nodes())}
    has_script = gen_m_script(cycles, unpaths, node2x, solution_file, port, script_file)
    
    # scan_fds = []
    if has_script:
        #run_matlab(script_file, port)
        #scan_fds = read_solution(os.path.join(opath, solution_file), node2x) + selfloop_nodes
        scan_fds = []
    else:
        scan_fds = selfloop_nodes
    return scan_fds

def gen_m_script(cycles, unpaths, node2x, solution_file, port, script_file):
    u'''
        @brief: 生成matlab脚本
        @params:
            cycles: a list of simple cycles 
            unpaths: a dict {(source, target):[list of all unblanced paths between source->target]}
            node2x: a dict {node: x(%d)}
            solution_file: a filename, tell the matlab to export the solution to this file_util
            port: a port number, tell the matlab to listen on this port for finishing signal
            script_file: a filename, print all the matlab statement to this file_util
        @return：
            True or False, indicates the script_file was generated or not
    '''
    #获取环的约束
    cycle_constaints = []
    for cycle in cycles:
        if len(cycle) == 1:
            continue
        variables = [node2x[node] for node in cycle]
        cycle_constaints.append("+".join(variables) + "<= %d;..." % (len(variables)-1))

    ##TODO:完善不平衡路径约束
    unpath_constraints = []
    ##获取不平衡路径的约束
    for (source, target), paths_between in unpaths.iteritems():
        # length: [paths]
        length_dict = {}
        # 把路径按照长度来归类.同一个长度的不平衡路径全部乘起来，称之为Ki
        for upath in paths_between:
            length = len(upath) 
            string = tuple([node2x[node] for node in upath])
            if length not in length_dict:
                length_dict[length] = [string]
            else:
                length_dict[length].append(string)
        #[paths][paths][paths]
        length_list = length_dict.values()
        products = []
        #print "%% (%s, %s)" % (source, target)
        for i in range(0, len(length_list)-1):
            for j in range(1, len(length_list)):
                for path_in_group_i in length_list[i]:
                    for path_in_group_j in length_list[j]:
                        products.append(set(path_in_group_i).union(set(path_in_group_j)))
        for product in products:
            unpath_constraints.append("+".join(product) +\
                                      "<= %d;..." % (len(product)-1))
    #如果两个约束都是空的，直接返回false
    if not cycle_constaints and not unpath_constraints:
        return False
    # 输出matlab脚本    
    with StdOutRedirect(script_file):
        print "x = binvar(1, %d);" % len(node2x)
        print ''' ops = sdpsettings('solver','bnb','bnb.solver','fmincon','bnb.method',...
                      'breadth','bnb.gaptol',1e-8,'verbose',1,'bnb.maxiter',1000,'allownonconvex',0);
        '''
        print "obj = x;"
        print "constraints = [",
        if cycle_constaints:
            print os.linesep.join(cycle_constaints)
        if unpath_constraints:
            print os.linesep.join(unpath_constraints)
        print "];"
        print "solvesdp(constraints, obj, ops);"
        print "fid = fopen('%s','w');" % solution_file
        print "for i = 1:%d" % len(node2x)
        print "    fprintf(fid, 'x(%d)  %d\\n', i, double(x(i)));"
        print "end"
        print "t = tcpip('localhost', %d, 'NetworkRole', 'client');" % port
        print "fopen(t)"
        print "fwrite(t, 'valid')"
        print "if (fread(t) == 105 )"
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
    os.system("matlab -nodesktop -sd  %s -r %s" % (opath, basename))
    connection, addr = server_socket.accept()
    if connection.recv(100) == "valid":
        print "Matlab excuted OK!"
        # send an i to close Matlab
        connection.send("i")
    connection.close()
    server_socket.close()
    return

if __name__ == "__main__":
    PATH = raw_input("plz enter vm files path:")
    if not os.path.exists(PATH):
        print "Error: %s doesn't exists" % PATH
        sys.exit(-1)
    OPATH = os.path.join(PATH, "ESMatlab")
    if not os.path.exists(OPATH):
        os.mkdir(OPATH)
    for eachVm in vm_files2(PATH):
        graph = get_graph(eachVm)
        esgrh = ESGraph(graph)
        get_scan_fds(esgrh, OPATH)
