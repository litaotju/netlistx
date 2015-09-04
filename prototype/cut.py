# -*- coding:utf-8 -*- 
import networkx as nx

def cut(graph):
    ''' parame: 
            graph:a nx.DiGraph obj
	    return:
		    cs : edge cut set of the graph
		    g1 , g2 : subgraphs induced by cs
	
    '''
    debug = True
    assert isinstance(graph, nx.DiGraph), "Input_para.__class__  %s " % graph.__class__
    assert graph.number_of_nodes() > 1,   "Number of nodes: %d" % graph.number_of_nodes
    if debug: print "\nDigraph Edges Are:\n    %s" % str(graph.edges())
    unigraph = nx.Graph(graph)           #将输入的图转为无向图
    cs = nx.minimum_edge_cut(unigraph)   #找出该无向图的minimum edge cut -> CS
    #balance函数调用cut前，graph一定是一个un-balance 结构，所以一定有CUT?
    if not cs:
        raise Exception,"Cut Set of this graph is Empty"
    #CS中的边，可能不存在于原来的有向图中，所以需要将这种边的方向颠倒
    #将所有real edge,存到RCS中
    rcs = []
    original_edges = graph.edges()
    for eachEdge in cs:
        if not eachEdge in original_edges:
            eachEdge = (eachEdge[1], eachEdge[0]) #调换方向
        rcs.append(eachEdge)
    graph.remove_edges_from(rcs)			      #在原图中移除CS
    if debug: print "Edge Cut Set RCS :\n    %s" % str(rcs)
    if debug: print "After remove RCS :\n    %s" % str(graph.edges())
    
    # 移除RCS中的边之后得到的两个Weakly Connected Subgraph
    glist = []
    for eachCntComp in nx.weakly_connected_component_subgraphs(graph):
		#找到移除CS后的两个弱连接分量
        glist.append(eachCntComp)
        if debug:
            print "Weakly CC %d:" % len(glist)
            print "    nodes:%s" % eachCntComp.nodes() 
            print "    edges:%s" % eachCntComp.edges()
    assert len(glist) == 2
    return rcs, glist[0], glist[1]

#-------------------------------------------------------------------------------------
def __test():
    '''
    '''
    g = nx.DiGraph()
    g.add_edges_from([(0,2),(1,2),(2,4),(2,5),(5,3),(5,4)])
    cs, gs, gd= cut(g)
    g2 = nx.DiGraph()
    g2.add_edge(0,1)
    cs,gs,gd = cut(g2)
if __name__ == "__main__":
    __test()
