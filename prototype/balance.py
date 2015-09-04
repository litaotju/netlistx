# -*- coding:utf-8 -*- #
from cut import cut
from check import check
import networkx as nx

def balance(graph):
    '''parame: graph, a DAG its.__class__ == nx.DiGraph
       return: r,     removed edges set so makr the input graph a b-structure
    '''
    # 只处理整数形式的图，每一个整数对应的节点可以在后面查到
    # 输入进来的图应该是连通的，如果存在非连通图，minimum_edge_cut就会产生问题
    assert nx.is_directed_acyclic_graph(graph),\
        "The target graph you want to banlance is not a DAG"
    r = [] # removed set
    if check(graph):
        return r
    #非B-Stucture时，一直循环下去
    # BUGY: 如果cs为空呢，那么不可能有两个图返回来，这时候怎么办
    print "\nCutting Graph"
    cs, g1, g2 = cut(graph) 
    r = balance(g1) + balance(g2) + cs
    csl = []
    for eachEdge in cs:
        under_check_graph = graph.copy()
        under_check_graph.remove_edges_from(r)
        under_check_graph.add_edges_from(csl)
        under_check_graph.add_edge(eachEdge[0],eachEdge[1])
        if check(under_check_graph):
            print "Edge: %s added back" % str(eachEdge)
            csl.append(eachEdge)
            graph.add_edge(eachEdge[0],eachEdge[1])
    for eachEdge in csl:
        r.remove(eachEdge)
    print "Removed Edge Set: %s" % str(r)
    return r

#------------------------------------------------------------------------------

def __test_case(g):
    '''Test with a Specific graph
    '''
    print "Balancing Graph"
    r = balance(g)
    g.remove_edges_from(r)
    assert check(g) ,"Graph is not balanced"
    print "Find a R, and result B-structure"
    print "    removed   : %s" % r
    print "    left edges: %s" % g.edges()

def __test():
    g1 = nx.DiGraph()
    g1.add_edges_from([(0,2),(1,2),(2,3),(0,3)])
    __test_case(g1)
    
    # g2 is Fig6 in 89 Ballast
    g2 = nx.DiGraph()
    edge_list =[(0,3),(1,3),(2,4),(3,4),(3,5),(4,5),(4,6),\
                (5,6),(5,7),(6,8),(7,9),(8,9)] 
    g2.add_edges_from(edge_list)
    __test_case(g2)
    
    g3 = nx.DiGraph()
    g3.add_edges_from([(0,2),(0,3),(1,2),(1,3),(2,3)])
    __test_case(g3)

    g4 =nx.DiGraph()
    g4.add_edges_from([(0,2),(1,2),(2,3),(3,4),(4,5),(1,5)])
    __test_case(g4)

if __name__ == '__main__':
    __test()