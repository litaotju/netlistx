# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 15:37:28 2015
@author: litao
"""
include_pipo = False
verbose = True
##pipo 包含在里面的话,画图的就有顺序,就可以显示pipo
paint_order = include_pipo
display_pipo = include_pipo

import matplotlib.pylab as plt
import networkx       as nx
import netlist_util   as nu
<<<<<<< HEAD
from   graph_util    import circuit_graph

=======
from   graph_util    import circuit_graph 
>>>>>>> master
###############################################################################
def get_graph(fname):

    info=nu.vm_parse(fname)
    m_list=info['m_list']

    nu.mark_the_circut(m_list,verbose)
    nu.rules_check(m_list)

    # 原图
    g1 = circuit_graph(m_list,include_pipo)
    g1.info()
    # cloud_reg 图
    cloud_reg1=g1.get_cloud_reg_graph()
    cloud_reg1.info()
<<<<<<< HEAD
    cloud_reg1.check_rules()
    
    # BALLAST
#    import ballast
#    bobj = ballast.Ballaster()
#    bobj.reg2arc(cloud_reg1)
#    print "After reg2arc "
#    print nx.info(cloud_reg1)
#    bobj.feedbackset(cloud_reg1)
    
    # S图
#    s1=g1.get_s_graph()
#    print nx.info(s1)

=======
    if not cloud_reg1.check_rules():
        raise AssertionError
#    s2=s_graph(fname,g1.edge_set,g1.vertex_set,g1.include_pipo,verbose=False)
#    s2.info()
    s1=g1.get_s_graph()
    print nx.info(s1)
    s_graph_reduction(s1)
#   ##显示原始的电路结构图
>>>>>>> master
#    plt.figure("Original_Circut")
#    g1.paint()
#    plt.figure("Cloud_reg")
#    cloud_reg1.paint()
#    plt.figure("S_Graph")
#    s1.paint(display_pipo,paint_order)
<<<<<<< HEAD
    return True

=======

    return True
    
###############################################################################    
def s_graph_reduction(g1):
    '''
        >>>8 reduction strategy of the cloud and reg graph
    '''
    g=nx.DiGraph()
    g=g1
    ind_dict=g.in_degree()
    oud_dict=g.out_degree()
    loop_nodes=g.nodes_with_selfloops()
    cut_set=[]
    cut_set+=loop_nodes
    for eachNode in g.nodes():
        if ind_dict[eachNode]==0 or oud_dict[eachNode]==0:
            g.remove_node(eachNode)
    for eachNode in g.nodes():
        if ind_dict[eachNode]==1 and eachNode not in loop_nodes:
            tmp=g.predecessors(eachNode)
            #merge
            assert len(tmp)==1
            if g.has_node(tmp[0]):
                g.remove_node(tmp[0])
                tmp_edge=g.out_edges(eachNode)
                for eachEdge in tmp_edge:
                    eachEdge=(tmp,eachEdge[1])
                g.add_edges_from(tmp_edge)
        elif oud_dict[eachNode]==1 and eachNode not in loop_nodes:
            tmp=g.successors(eachNode)
            #merge
            assert len(tmp)==1
            if g.has_node(tmp[0]):
                g.remove_node(tmp[0])
                tmp_edge=g.in_edges(eachNode)
                for eachEdge in tmp_edge:
                    eachEdge=(eachEdge[0],tmp)
                g.add_edges_from(tmp_edge)
    for eachNode in g.nodes_with_selfloops():    
        g.remove_node(eachNode)
    print nx.info(g)
    return True
>>>>>>> master
###############################################################################
if __name__=="__main__":
    fname= raw_input("plz enter fname:")
    get_graph(fname)