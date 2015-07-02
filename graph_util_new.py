# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
"""
import os.path
import netlist_util as nu
import circut_class as cc
###############################################################################
def get_edge_vertex(m_list,verbose=False):
    '---this func is to construct a s-graph of a circut---'
    pipo_vertex_list=[]
    prim_vertex_list=[]
    vertex_set=[]
    
    pi_edge_list=[]
    po_edge_list=[]
    prim_edge_list=[]
    edge_set=[]
    ###########################################################################
    #------------module vertex
    prim_vertex_list=m_list[1:]
    pipo_vertex_list=m_list[0].port_list
    vertex_set=prim_vertex_list+pipo_vertex_list
    ###########################################################################
    #edge
    #-----------PI PO edge excluding clock and  reset
    print "Process: searching PI and PO edges..."
    for eachPrim in prim_vertex_list:
        for eachPort in eachPrim.port_list:
            for eachPPort in pipo_vertex_list:
                #信号名称等于端口名称,可能prim port的信号是Pipo的某一bit
                if eachPort.port_assign.name==eachPPort.port_name:
                    cnt={'connection':eachPort.port_assign.name}                    
                    if eachPPort.port_type=='input':
                        assert eachPort.port_type in ['input','un_kown','clock'],\
                            (":port:%s,port_type:%s"%(eachPort.port_name,eachPort.port_type))
                        pi_edge_list.append([[eachPPort,eachPrim],[eachPPort,eachPort],cnt])
                    else:
                        if eachPort.port_type=='output':
                            po_edge_list.append([[eachPrim,eachPPort],[eachPort,eachPPort],cnt])
                        else:
                            prim_edge_list.append([[eachPPort,eachPrim],[eachPPort,eachPort],cnt])
    for eachPrim in prim_vertex_list:
        for eachPrim2 in prim_vertex_list:
            if eachPrim2==eachPrim:
                continue
            else:
                p_set=set(eachPrim.port_assign_list)
                p_set2=set(eachPrim2.port_assign_list)
                if p_set.intersection(p_set2):
                    for eachPort in eachPrim.port_list:
                        for eachPort2 in eachPrim2.port_list:
                            if eachPort2.port_assign.string==eachPort.port_assign.string and\
                                    eachPort2.port_type!=eachPort.port_type:
                                cnt_dict={"connection":eachPort.port_assign.string}
                                if eachPort.port_type=='input':
                                    prim_edge_list.append([[eachPrim,eachPrim2],[eachPort,eachPort2],cnt_dict])
                                else:
                                    prim_edge_list.append([[eachPrim2,eachPrim],[eachPort2,eachPort],cnt_dict])
                else:
                    continue


    #--------merge all the edge
    edge_set=pi_edge_list+po_edge_list+prim_edge_list
    print 'Note: get_edge_vertex() successfully !'
    if verbose:
        for eachVertex in vertex_set:
            eachVertex.__print__()
        for eachEdge in edge_set:
            print eachEdge[2]['connection']
    return vertex_set,edge_set

