# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
class  circuit_graph
"""

import networkx as nx
import class_circuit as cc

def vertex_in_graph(vertex,graph):
    '''
        判断一个cc.module类型的vertex是否在一个nx.Graph或者nx.DiGraph图中
        判断的标准是检查图中是否有相同.cellref 相同.name的节点，
        需要这个函数的原因是nx.connected_component_subgraphs()返回的子图是对节点的深度复制.
        返回值要么是None,要么是vertex在graph中对应的节点
    '''
    assert isinstance(vertex,cc.circut_module)
    assert isinstance(graph,(nx.DiGraph,nx.Graph))
    assert len(graph)>0
    flag=None
    for eachNode in graph.nodes_iter():
        if isinstance(eachNode,cc.circut_module):
            flag1=(eachNode.cellref==vertex.cellref)
            flag2=(eachNode.name==vertex.name)
            flag=(flag1 and flag2)
            if flag:
                return eachNode
        else:
            continue
    return flag


    
def s_graph_reduction(g1):
    '''
        8 reduction strategy of the cloud and reg graph
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

