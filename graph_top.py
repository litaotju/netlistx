# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 15:37:28 2015
@author: litao
"""
include_pipo=False
verbose=True
##pipo 包含在里面的话,画图的就有顺序,就可以显示pipo
paint_order= include_pipo
display_pipo=include_pipo
##-----------------------------------------------
import matplotlib.pylab as plt
import netlist_util   as nu
import networkx as nx
from   graph_util    import circuit_graph 
from   graph_s_graph import s_graph

###############################################################################
def get_graph(fname):
    
    info=nu.vm_parse(fname)
    assert info
    m_list=info['m_list']
    nu.mark_the_circut(m_list,verbose)
    g1 = circuit_graph(m_list,include_pipo)
    print nx.info(g1)
#    g1.info()
#    ##显示原始的电路结构图
#    plt.figure("Original_Circut")
#    g1.paint()
#    
    cloud_reg1=g1.get_cloud_reg_graph()
    cloud_reg1.info()
#    plt.figure("Cloud_reg")
#    cloud_reg1.paint()

    
#    s1=s_graph(fname,g1.edge_set,g1.vertex_set,g1.include_pipo,verbose=False)
#    s1.info()
#    ##显示s-graph的结构
#    plt.figure("S_Graph")    
#    s1.paint(display_pipo,paint_order)
    return True
    
###############################################################################
if __name__=="__main__":
    fname= raw_input("plz enter fname:")
    get_graph(fname)