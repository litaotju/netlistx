# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 15:37:28 2015

@author: litao
"""
include_pipo=True
display_original=False

##pipo 包含在里面的话,画图的就有顺序,就可以显示pipo
paint_order= include_pipo
display_pipo=include_pipo
##-----------------------------------------------
import graph_util     as gu
import netlist_parser as np
import netlist_util   as nu
from   s_graph_class import s_graph

###############################################################################
def get_graph(fname,display_original):
    
    info=np.parse_to_parse_list(fname)   
    m_list=[]
    m_list.append(info[0])
    m_list=m_list+info[3]
    nu.mark_the_circut(m_list)
    vertex_set,edge_set  = gu.get_edge_vertex(m_list,include_pipo,verbose=False)
    s1=s_graph(fname,edge_set,vertex_set,include_pipo,verbose=True)
    s1.info()
    ##显示原始的电路结构图
    if display_original:
        gu.display_graph(fname,vertex_set,edge_set,display_pipo)
    ##显示s-graph的结构
    else:
        s1.paint(display_pipo,paint_order)
    return True
    
###############################################################################
if __name__=="__main__":
    fname= raw_input("plz enter fname:")
    get_graph(fname,display_original)