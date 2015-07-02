# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 15:37:28 2015

@author: litao
"""
import graph_util_new as gu
#import file_util as fu
import netlist_parser as np
import netlist_util as nu
from s_graph_class import s_graph
###############################################################################

def get_graph(fname):
#    info = fu.extract_m_list(fname,verbose=False)
    info=np.parse_to_parse_list(fname)   
    m_list=[]
    m_list.append(info[0])
    m_list=m_list+info[3]
    nu.mark_the_circut(m_list)
    vertex_set,edge_set  = gu.get_edge_vertex(m_list,verbose=True)
#    s1=s_graph(fname,edge_set,vertex_set,vertex_set_dict,verbose=True)
#
#    s1.info()
#    s1.compu_fds_depth(verbose=True)
#    s1.paint(display_pipo=True)
    return True

if __name__=="__main__":
    fname= raw_input("plz enter fname:")
    get_graph(fname)