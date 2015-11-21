# -*-coding:utf-8 -*- #
import re
import os
import sys
import copy

import networkx as nx

from netlistx.file_util import vm_files

from netlistx.prototype.unbpath import unbalance_paths
from netlistx.graph.cloudgraph import *
from netlistx.graph.circuitgraph import CircuitGraph
from netlistx.graph.circuitgraph import get_graph

def upath_cycle(cr):
    '''@ param: cr, a nx.DiGraph,每一个节点必须有一个独特的name属性与其他节点不同
       @ return: upaths, cycles ,图中所有的不平衡路径和环
       @ brief: 将每一个图转化成节点的名字为节点的图，然后找出图中所有的不平衡路径和环
    '''
    tmp = {}
    for node in cr.nodes_iter():
        assert not tmp.has_key( node.name), \
            "Node:%s, has the same name with:%s, name:%s" % (node, tmp[node.name], node.name)
        tmp[node.name] = node

    namegraph = nx.DiGraph()
    for edge in cr.edges():
        namegraph.add_edge( edge[0].name, edge[1].name )
        
    upaths = unbalance_paths( namegraph)
    cycles = []
    for cycle in nx.simple_cycles(namegraph):
        cycles.append( cycle)
    return upaths, cycles

def convert2opt(cr, upaths, cycles):
    '''@param: cr, a graph, every node is a nx.DiGraph obj
               eweight, a dict, cr's edge -> weight
               upaths,  a dict, (s, t )   -> [ all unbalance paths bwt (s, t)]
               cycles,  a list, [ simple cycle of cr ]
        转化成Matlab求解的方法,并且打印要求解的问题的matlab程序
    '''
    ewight = cr.arcs 

    names ={ node:node.name for node in cr.nodes() }
    namewight = {}
    for edge, fds in ewight.iteritems():
        name0 = names[ edge[0] ]
        name1 = names[ edge[1] ]
        assert not namewight.has_key( (name0, name1) )
        namewight[(name0, name1)] = len(fds)

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
            back_edge = (cycle[-1], cycle[0])
            all_edges[ back_edge ] = namewight[ back_edge ]
            edges.append( back_edge )
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
    print "%%All self_loopfd count is: %d" % self_loopfd_count
    
    if (not cycle_const) and (not unbalance_const):
        print "%%Graph Is blance after self-loop remove."
        return None

    # 准备进行权重和约束的输出
    cnt = 0
    sorted_wight = []
    for edge, wight in all_edges.iteritems():
        cnt += 1 
        edge2x[ edge ] = "x(%d)" %cnt
        print "%% x%d: %s -> %s" % (cnt, edge[0], edge[1])
        sorted_wight.append( wight)
    print "x = binvar(1, %d);" % len(all_edges)

    SDPSETTING = '''
    ops = sdpsettings('solver','bnb','bnb.solver','fmincon','bnb.method',...
                  'breadth','bnb.gaptol',1e-8,'verbose',1,'bnb.maxiter',1000,'allownonconvex',0);
    '''
    print SDPSETTING
    #权重的字符串形式
    print "%% Weight of Edges"
    print "W = ", str(sorted_wight ) , ";"
    
    print "obj = -x*W';"
    print "constraints = [..."
    #环约束的字符串形式
    cycle_string_const = [] 
    for cycle in cycle_const:
        xs = []
        for edge in cycle:
            xs.append( edge2x[edge])
        string = "*".join( xs )
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
            xs = []
            for edge in upath:
                xs.append( edge2x[edge] )
            string = "*".join( xs)
            if not length_dict.has_key( n ):
                length_dict[n] = string
            else:
                length_dict[n] = length_dict[n]+"*"+string
        
        length_list = length_dict.values()
        print "%% (%s, %s)" % (s,t)
        print "\n".join([ "%% k%d: %s" %(i+1, length_list[i] ) \
                            for i in range(0, len(length_list) )] )
        n = len( length_list )
        assert n >= 2
        #将不同的Ki两两相乘
        for i in range(0, n-1):
            for j in range(i+1, n):
                print "%% k%d * k%d" %(i, j)
                print length_list[i]+"*"+length_list[j] + "<= 1/100000;..." 
    print "];"
    if not unbalance_const:
        print "%% There is no unbalance path in this graph. So Opt is same with Ballast"
    SOLVE   = '''solvesdp(constraints,obj, ops);'''
    DISPLAY = '''for i = 1:%d\n fprintf('x %%d  ',i);\n display(x(i));\n end''' % len(all_edges )
    ALL_FD = sum([ len(fdlist) for fdlist in ewight.itervalues()])
    RUSULT = "display( sum(W)-x*W'+%d );" % self_loopfd_count
    print "%%All fd number is: %d"  % ALL_FD 
    print SOLVE
    print DISPLAY
    print "%%the number to scan:"
    print RUSULT
    return None

if __name__ == "__main__":
    path = raw_input("plz enter path>")
    opath =  os.path.join( path, "OptMatlab")  #存放matlab脚本的目录
    if not os.path.exists(): os.mkdir( opath )
    for eachvm in vm_files( path ):
        g = get_graph( os.path.join(path, eachvm) )
        cr = CloudRegGraph( g )
        cr.info()
        upaths, cycles = upath_cycle( cr)

        console = sys.stdout 
        mscript =  open( os.path.join(opath, g.name +".m") ,'w')
        sys.stdout = mscript
        convert2opt(cr, upaths, cycles)
        sys.stdout = console
        mscript.close()
