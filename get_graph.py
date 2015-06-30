# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 15:37:28 2015

@author: litao
"""
import graph_util as gu
import file_util as fu
from s_graph_class import s_graph
###############################################################################

def get_graph(fname):
    fobj =open(fname)
    info = fu.extract_m_list(fname,verbose=False)
    m_list=info[0]
    vertex_set,vertex_set_dict,edge_set  = gu.get_edge_vertex(m_list,verbose=False)
    s1=s_graph(fname,edge_set,vertex_set,vertex_set_dict,verbose=True)

    s1.info()
    s1.compu_fds_depth(verbose=True)
    s1.paint(display_pipo=True)
    fobj.close()
    return True

if __name__=="__main__":
    fname= raw_input("plz enter fname:")
    get_graph(fname)