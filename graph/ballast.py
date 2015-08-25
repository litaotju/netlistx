# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 13:16:27 2015

@author: litao
@e-mail:litaotju@qq.com
@license: Free

"""
import networkx as nx
#import netlist.class_circuit as cc
from graph_util import CloudRegGraph


class Ballaster:
    '''
        util func for graph to get a b-structure,
        注意ballaster当中的函数都对整数型的节点的 图有效
    '''
    def __init__(self):   
        pass
    
    def reg2arc(self, graph):
        '''把所有的reg节点 ignore掉，将其前后相连'''
        arc = {}       
        for reg in graph.regs:
            prec = graph.predecessors(reg)
            succs = graph.successors(reg)
            graph.remove_node(reg)
            assert len(prec) <= 1 
            if len(prec) == 1 :
                assert isinstance(prec[0], nx.DiGraph)
            else:
                continue
            for succ in succs:
                if not isinstance(succ, nx.DiGraph):
                    assert isinstance(succ, cc.circut_module)
                    print "INfo:succ %s %s" % (succ.cellref, succ.name)
                graph.add_edge(prec[0], succ)
            arc[reg]=(prec, succs)
        return arc

    def __convert2intgraph(self, graph):
        ''' 
            拓扑图只是包含了节点以及他们的连接，所以在进行基于结构的算法时候只需要
            把图转换成每一个节点是独特的整数的图就可以了。
            同时返回每一个整数所对应的原图节点对象
        '''
        intgraph = nx.DiGraph()
        nodes = graph.nodes()
        for edge in graph.edges_iter():
            intedge = (nodes.index(edge[0]), nodes.index(edge[1]))
            intgraph.add_edge(intedge[0], intedge[1])
        return intgraph, nodes
        
    def feedbackset(self, graph):
        '''
        step1 找出给定的 cr 图的 feedback 集合
        '''
        #assert isinstance(graph,CloudRegGraph),"Error: % " % graph.__class__
        assert isinstance(graph, nx.DiGraph), "Type Error: % " % graph.__class__
        intgraph, node_mapping = self.__convert2intgraph(graph)
        graph.fas = []
        feedbackset_index = []
        for c in nx.simple_cycles(intgraph):
            print "Info: find cycle %s " % c
            edge = (c[0],c[1])
            if not edge in feedbackset_index: # 因为edge是一个整数型元组，所以这是对的
                feedbackset_index.append(edge)
        for index in feedbackset_index:
            graph.fas.append( (node_mapping[index[0]], node_mapping[index[1]]) )
        #graph.remove_nodes_from(graph.fas)
        return graph.fas
        
    def balance(self, graph):
        '''
        step2 把无环图 balancize
        '''
        set1 = []
        # TODO find the cut
        graph.remove_nodes(set1)
        return set1

    def check(self, graph):
        pass
    
if __name__ == '__main__':
    'test the ballaster'    
    b1 = Ballaster()
    g1 = nx.DiGraph()
    g1.add_path([0,1,2,0])
    g1.add_path([2,3,4,2])
    b1.feedbackset(g1)
    print g1.fas
    g2 = nx.DiGraph()
    g2.add_path([1,0,5,1])
    g2.add_path([5,1,3,5])
    g2.add_path([2,1,3,2])
    g2.add_path([5,4,3,5])
    b1.feedbackset(g2)
    print g2.fas
    