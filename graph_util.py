# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
"""
import networkx as nx
import matplotlib.pyplot as plt
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
                                    prim_edge_list.append([[eachPrim2,eachPrim],[eachPort2,eachPort],cnt_dict])
                                else:
                                    prim_edge_list.append([[eachPrim,eachPrim2],[eachPort,eachPort2],cnt_dict])
                else:
                    continue


    #--------merge all the edge
    edge_set=pi_edge_list+po_edge_list+prim_edge_list
    #edge_set的每一个元素是 一个([],[],{})类型的变量,
    #第一个列表存储prim,第二个存储port,第三个存储连接信号
    print 'Note: get_edge_vertex() successfully !'
    if verbose:
        for eachVertex in vertex_set:
            eachVertex.__print__()
        for eachEdge in edge_set:
            print eachEdge[2]['connection']
    return vertex_set,edge_set
###############################################################################
#画图,只画出基本的节点,边和标签,不判断图是什么类型的
#与s_graph class中定义的画图相比,没有层次化,只是spring_layout
def get_vertex_label(vertex_set):
    label_dict={}
    for eachVertex in vertex_set:
        if isinstance(eachVertex,cc.circut_module):
            label_dict[eachVertex]=eachVertex.cellref+" : "+eachVertex.name
        else:
            assert isinstance(eachVertex,cc.port)
            label_dict[eachVertex]=eachVertex.port_type+" : "+eachVertex.port_name
    return label_dict
    
def display_graph(name,vertex_set,edge_set):
    graph1=nx.DiGraph()
    graph1.add_nodes_from(vertex_set)
    for eachEdge in edge_set:
        graph1.add_edge(eachEdge[0][0],eachEdge[0][1])
    label_dict=get_vertex_label(vertex_set)
    ps=nx.spring_layout(graph1)
    nx.draw_networkx_nodes(graph1,pos=ps,nodelist=vertex_set,node_color='g')
    nx.draw_networkx_edges(graph1,ps)
    nx.draw_networkx_labels(graph1,ps,labels=label_dict)
    plt.savefig(name+".jpg")
    return True