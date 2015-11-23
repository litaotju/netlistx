# -*-coding:utf-8 -*- #
import re
import os
import sys
import copy
import time

import networkx as nx

from netlistx.file_util import vm_files, StdOutRedirect

from netlistx.prototype.unbpath import unbalance_paths
from netlistx.graph.cloudgraph import CloudRegGraph
from netlistx.graph.circuitgraph import CircuitGraph
from netlistx.graph.circuitgraph import get_graph

def get_namegraph(cr):
    tmp = {}
    for node in cr.nodes_iter():
        assert not tmp.has_key( node.name), \
            "Node:%s, has the same name with:%s, name:%s" % (node, tmp[node.name], node.name)
        tmp[node.name] = node
    namegraph = nx.DiGraph()
    for edge in cr.edges():
        namegraph.add_edge( edge[0].name, edge[1].name )
    return namegraph

def upath_cycle(namegraph):
    '''@ param: cr, a nx.DiGraph,每一个节点必须有一个独特的name属性与其他节点不同
       @ return: upaths, cycles ,图中所有的不平衡路径和环
       @ brief: 将每一个图转化成节点的名字为节点的图，然后找出图中所有的不平衡路径和环
    '''       
    upaths = unbalance_paths( namegraph)
    cycles = []
    for cycle in nx.simple_cycles(namegraph):
        cycles.append( cycle)
    return upaths, cycles

def convert2opt(cr, upaths, cycles ):
    '''@param: cr, a graph, every node is a nx.DiGraph obj
               eweight, a dict, cr's edge -> weight
               upaths,  a dict, (s, t )   -> [ all unbalance paths bwt (s, t)]
               cycles,  a list, [ simple cycle of cr ]
        转化成Matlab求解的方法,并且打印要求解的问题的matlab程序
    '''
    ewight = cr.arcs 
    namewight = {}
    for edge, fds in ewight.iteritems():
        assert not namewight.has_key( ( edge[0].name, edge[1].name) )
        namewight[ ( edge[0].name, edge[1].name ) ] = len(fds)
    edge2x = {}       #名称字典,键为名称边，值为X变量的索引
    all_edges = {}    #权重字典,键为名称边，值为权重
    cycle_const = []

    self_loops = []    
    # 下面进行cycles列表的获取
    for cycle in cycles:
        if len(cycle) == 1:
            self_loops.append( (cycle[0],cycle[0]) )
        else:
            edges = []
            for i in range(0, len(cycle)-1 ):
                edge = (cycle[i], cycle[i+1]) 
                edges.append( edge )
                all_edges[ edge ] = namewight[ edge ]
            edge = (cycle[-1], cycle[0])
            all_edges[ edge ] = namewight[ edge ]
            edges.append( edge )
            cycle_const.append( edges )
    
    # 下面字典的每一个Key是（s,t）tuple，值是s.t之间的所有路径的列表
    unbalance_const = {}
    for (s,t), path_bwt in upaths.iteritems():
        if s is t or s == t:
            continue
        unbalance_const[ (s,t) ] = []
        for upath in path_bwt:
            edges = []
            for i in range(0, len(upath)-1):
                edge = (upath[i], upath[i+1])
                edges.append( edge )
                all_edges[ edge ] = namewight[ edge ]
            unbalance_const[ (s,t) ].append( edges )
    
    # Self-loop 数目
    self_loopfd_count = 0
    for loop in self_loops:
        print "%%Self-loop: %s, weight:%d" % (loop, namewight[loop] )
        self_loopfd_count += namewight[loop]
    print "%%All self_loop FD count is: %d" % self_loopfd_count
    
    if (not cycle_const) and (not unbalance_const):
        print "%%Graph Is blance after self-loop remove."
        return None

    # 准备进行权重和约束的输出
    cnt = 0
    sorted_weight = []
    for edge, weight in all_edges.iteritems():
        cnt += 1 
        edge2x[ edge ] = "x(%d)" %cnt
        print "%% x%d: %s -> %s, weight: %d" % (cnt, edge[0], edge[1], weight)
        sorted_weight.append( weight)

    print "x = binvar(1, %d);" % len(all_edges)
    print '''
    ops = sdpsettings('solver','bnb','bnb.solver','fmincon','bnb.method',...
                  'breadth','bnb.gaptol',1e-8,'verbose',1,'bnb.maxiter',1000,'allownonconvex',0);
    '''
    #权重的字符串形式
    print "%% Weight of Edges"
    print "W = ", str(sorted_weight ) , ";"
    
    print "obj = -x*W';"
    print "constraints = [..."
    #环约束的字符串形式
    cycle_string_const = [] 
    for cycle in cycle_const:
        string = "*".join( [ edge2x[edge] for edge in cycle ] )
        string = string+ "<= 1/100000 ;..."
        cycle_string_const.append( string )
    print "%% Cycle Constraits Are:"
    print "\n".join( cycle_string_const)

    #不平衡路径约束的字符串形式
    print "%% Unbalance Constraints Are:"
    unbalance_string_const = [] 
    for (s, t), paths_between in unbalance_const.iteritems():
        length_dict = {}
        # 把路径按照长度来归类.同一个长度的不平衡路径全部乘起来，称之为Ki
        for upath in paths_between:
            n = len( upath ) 
            string = "*".join( [ edge2x[edge] for edge in upath ] )
            if not length_dict.has_key( n ):
                length_dict[n] = string
            else:
                length_dict[n] = length_dict[n]+"+"+string
        
        length_list = length_dict.values()
        print "%% (%s, %s)" % (s,t)
        print "\n".join([ "%% k%d: %s" %(i+1, length_list[i] ) \
                            for i in range(0, len(length_list) )] )
        n = len( length_list )
        assert n >= 2
        #将不同的Ki两两相乘
        for i in range(0, n-1):
            for j in range(i+1, n):
                print "%% k%d * k%d" %(i+1, j+1)
                print "(" + length_list[i] + ")*(" + length_list[j] + ")<= 1/100000;..." 
    print "];"
    if not unbalance_const:
        print "%% There is no unbalance path in this graph. So Opt is same with Ballast"
  
    ALL_FD = sum([ len(fdlist) for fdlist in ewight.itervalues()])
    print "%%All fd number is: %d"  % ALL_FD
    print "tic;"
    print "solvesdp(constraints,obj, ops);"
    print "t = toc;"
    print "toc"
    print "fid = fopen('%s_partialOptScanEdge.txt','w');" % cr.name[:-11]
    print "for i = 1:%d" % len(all_edges )
    print "    fprintf(fid, 'x(%d)  %d\\n', i, double(x(i)));"
    print "end" 
    print "result = double(x);"
    print "fprintf(fid, '//all fd:%d\\n');" % ALL_FD
    print "%%the number to scan:"
    print "fprintf('scan fd:%%d\\n', double(sum(W)-x*W'+%d ));" % self_loopfd_count
    print "fprintf(fid,'//scan fd:%%d\\n', double(sum(W)-x*W'+%d ));" % self_loopfd_count
    print "fprintf(fid,'//time spent solve sdp: %.4f', t);"
    print "fclose(fid);"
    print "exit();"
    return edge2x


def readsolution(solutionfile, edge2x):
    '''读取matlab的计算结果，得到需要变为扫描的边
    '''
    scan_edges = []
    x2edge = { val:key for key,val in edge2x.iteritems() }
    with open(solutionfile,'r') as solution:
        for line in solution:
            if line.startswith("//"): continue
            (x, val) = tuple(line.strip().split())
            if int(val) == 0:
                scan_edges.append( x2edge[x] )
    return scan_edges

def get_scan_fds(cr, path):
    '''由图找约束，由约束得m脚本，运行m脚本得解，由解得扫描触发器
    '''
    basename = cr.name[:-11]

    namegraph = get_namegraph(cr)
    upaths, cycles = upath_cycle( namegraph )

    opath =  os.path.join( path, "OptMatlab")  #存放matlab脚本的目录
    if not os.path.exists( opath ):
        os.mkdir( opath )    
    with StdOutRedirect( os.path.join(opath, basename +".m") ):
        edge2x = convert2opt(cr, upaths, cycles)

    solutionfile = os.path.join(opath, "%s_partialOptScanEdge.txt" % basename)
    if os.path.exists(solutionfile):
        os.remove( solutionfile )
        print solutionfile, " removed"

    os.system("matlab -nodesktop -sd  %s -r %s" % ( opath, basename ) )

    print "Matlab excuting..."
    #注意线程安全，matlab写完了文件之后才能读
    while( not os.path.exists(solutionfile) ):
        time.sleep(30)
        print "Waiting for matlab result"
    time.sleep(60)
    print "Matlab result OK!" 
    name_edge = {(edge[0].name, edge[1].name): edge for edge in cr.arcs}
    scan_fds = []
    for edge in readsolution( solutionfile, edge2x):
        scan_fds += cr.arcs[ name_edge[edge] ]
        cr.remove_edge( name_edge[edge][0], name_edge[edge][1] )

    #import partialBallast as pb
    #if not pb.__check(cr):
    #    print "Wrong Answer"
    return scan_fds

if __name__ == "__main__":
    path = raw_input("plz enter path>")
    for eachvm in vm_files( path ):
        g = get_graph( os.path.join(path, eachvm) )
        cr = CloudRegGraph( g )
        cr.info()
        scan_fds = get_scan_fds(cr, path)
        with StdOutRedirect( os.path.join(path, cr.name[:-11]+"_optScanFDs.txt")):
            print "\n".join([ "%s %s" % (fd.cellref, fd.name) for fd in scan_fds] )