# -*- coding: utf-8 -*-

import sys
import os
import time
import networkx as nx

# user-defined module
import netlistx.circuit as cc
from netlistx.file_util    import vm_files

from netlistx.graph.cloudgraph      import CloudRegGraph
from netlistx.graph.circuitgraph    import get_graph
from netlistx.prototype.fas         import comb_fas
from netlistx.scan.scanapp import ScanApp

__all__ = [ "balance", "ballast" ]

def balance( graph):
    assert nx.is_directed_acyclic_graph(graph),\
        "The target graph you want to banlance is not a DAG"
    r = [] # removed set
    if __check(graph):
        return r
    weight = nx.get_edge_attributes( graph, 'weight')
    assert len(weight) == graph.number_of_edges()
    cs, g1, g2 = __cut(graph) 
    r = balance(g1) + balance(g2) + cs
    csl = []
    cs.sort( key = lambda x: weight[x], reverse = True)
    for i in range( 0, len(cs) ):
        eachEdge = cs[i]
        under_check_graph = graph.copy()
        under_check_graph.remove_edges_from(r)
        under_check_graph.add_edges_from(csl)
        under_check_graph.add_edge(eachEdge[0], eachEdge[1])
        if __check(under_check_graph):
            csl.append(eachEdge)
            graph.add_edge(eachEdge[0],eachEdge[1], {'weight':weight[eachEdge] } )
    for eachEdge in csl:
        r.remove(eachEdge)
    return r
  
def __check( graph ):
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
#--------------------------------------------------------------------------------
    
def __cut(graph):
    ''' param: 
            graph:a nx.DiGraph obj
	    return:
		    cs : edge cut set of the graph
		    g1 , g2 : subgraphs induced by cs
	
    '''
    assert isinstance(graph, nx.DiGraph), "graph class: %s " % graph.__class__
    assert graph.number_of_nodes() > 1,   "Number of nodes: %d" % graph.number_of_nodes()
    unigraph = nx.Graph( graph )          
    cs = nx.minimum_edge_cut( unigraph ) 
    if not cs:
        raise Exception,"Cut Set of this graph is Empty"

    #CS中的边，可能不存在于原来的有向图中，所以需要将这种边的方向颠倒
    #将所有real edge,存到RCS中
    rcs = []
    for eachEdge in cs:
        if not graph.has_edge( eachEdge[0], eachEdge[1] ):
            eachEdge = (eachEdge[1], eachEdge[0]) #调换方向
        rcs.append(eachEdge)
    graph.remove_edges_from(rcs)
    glist = []
    for eachCntComp in nx.weakly_connected_component_subgraphs(graph, copy = False):
        glist.append(eachCntComp)
    assert len(glist) == 2
    return rcs, glist[0], glist[1]

def convert2int( graph):
    '''把传进来的图转化为整数图
    '''
    intgraph = nx.DiGraph(name = graph.name + "_intgraph" )
    map = {}
    invmap = {}
    i = 0
    for node in graph.nodes_iter():
        map[node] = i
        invmap[i] = node
        i += 1
    oweight = nx.get_edge_attributes(graph, 'weight' )
    for edge in graph.edges_iter():
        intedge = ( map[ edge[0] ], map[ edge[1] ] )
        intgraph.add_edge(intedge[0], intedge[1], weight = oweight[edge] )
    return intgraph, map, invmap

def ballast( crgraph):
    '''Ballast方法的完整实现
    '''
    intgraph, map, invmap = convert2int( crgraph )
    comfas = []
    r = []

    timecycle = 0
    timebal = 0

    for subgraph in nx.weakly_connected_component_subgraphs( intgraph ):
        start = time.clock()
        comfas += comb_fas( subgraph)
        tcycle = time.clock()
        
        r += balance( subgraph )
        tbal = time.clock()
        
        timecycle += (tcycle- start)
        timebal += (tbal - tcycle)
    fobj = open("test\\timeStats.txt", 'a')
    fobj.write( "%s , cycle:%.3f, bal:%.3f, total:%.3f\n"\
             %( crgraph.name[:-11], timecycle, timebal, (timecycle + timebal)) )
    fobj.close()

    #print "CombFAS:", comfas
    #print "R:", r
    if not r:
        print "Info: %s is blance after cycle removed" % crgraph.name
    else:
        print "Info: %d edges removed in unblanced paths." % len(r)
    scanfds = []
    for edge in comfas + r:
        realedge = invmap[edge[0]], invmap[edge[1]]
        scanfds += crgraph.arcs[realedge]
    return scanfds

def testA():
    '''在这个例子里balance是最优的
    '''
    a = nx.DiGraph()
    a.add_edge(1, 2, weight = 100)
    a.add_edge(1, 3, weight = 2)
    a.add_edge(1, 4, weight = 1)
    a.add_edge(3, 2, weight = 2)
    a.add_edge(4, 2, weight = 1)
    r = balance(a)
    print(r)

def testB():
    '''本例论证了ballast方法的非最优性
    '''
    a = nx.DiGraph()
    a.add_edge(1, 2, weight = 3)
    a.add_edge(1, 3, weight = 2)
    a.add_edge(1, 4, weight = 2)
    a.add_edge(3, 2, weight = 2)
    a.add_edge(4, 2, weight = 2)
    r = balance(a)
    print(r)


class BallastApp(ScanApp):
    u'''可直接运行此App，获得Ballast方法的扫描触发器
    '''
    def __init__(self, name="Ballast"):
        super(BallastApp, self).__init__(name)

    def _get_scan_fds(self, vm):
        g = get_graph(vm)
        g.info()
        cr = CloudRegGraph(g)
        cr.info()
        self.fds = filter(cc.isDff, g.nodes_iter())
        self.scan_fds = ballast(cr)

if __name__ == "__main__":
    BallastApp().run()

