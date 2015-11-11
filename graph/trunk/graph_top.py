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

# user-defined module
import netlistx.netlist_util   as nu
from netlistx.exception import *

from circuitgraph    import CircuitGraph
from crgraph         import CloudRegGraph
from ballast         import Ballaster

###############################################################################
def get_graph(fname):

    info   = nu.vm_parse(fname)
    m_list = info['m_list']
    nu.mark_the_circut(m_list)
    nu.rules_check(m_list)

    # 原图
    g1 = CircuitGraph(m_list, include_pipo = True)
    g1.info()
    
    # cloud_reg 图
    cloud_reg1=CloudRegGraph(g1)
    cloud_reg1.info()
    
    # BALLAST
    ballas = Ballaster(cloud_reg1)
    cloud_reg1.info()
    print "After Reg2Arc"
    print nx.info(ballas.intgraph)
    ballas.feedbackset()
    print "After removed FAS "
    print nx.info(ballas.intgraph)
#
#    # S图
#    s1=g1.get_s_graph()
#    print nx.info(s1)
#    
#    #打印 画图
#    plt.figure("Original_Circut")
#    g1.paint()
#    plt.figure("Cloud_reg")
#    cloud_reg1.paint()
#    plt.figure("S_Graph")
#    s1.paint(display_pipo,paint_order)

    return True

###############################################################################
if __name__=="__main__":
    fname= raw_input("plz enter fname:")
    get_graph(fname)