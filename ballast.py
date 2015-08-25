# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 13:16:27 2015

@author: litao
@e-mail:litaotju@qq.com
@license: Free

"""
import networkx as nx
import class_circuit as cc
from graph_util import cloud_reg_graph


class Ballaster:
    '''
        util func for graph to get a b-structure
    '''
    def reg2arc(self, graph):
        '''把所有的reg节点 ignore掉，将其前后相连'''
        arc = {}       
        for reg in graph.regs:
            prec = graph.predecessors(reg)
            assert len(prec) == 1 and isinstance(prec[0], nx.DiGraph)
            succs = graph.successors(reg)
            graph.remove_node(reg)
            for succ in succs:
                if not isinstance(succ, nx.DiGraph):
                    assert isinstance(succ, cc.circut_module)
                    print "INfo:succ %s %s" % (succ.cellref, succ.name)
                graph.add_edge(prec[0], succ)
            arc[reg]=(prec, succs)
        return arc
        
    def feedbackset(self, graph):
        '''
        step1 找出给定的 cr 图的 feedback 集合
        '''
        assert isinstance(graph,cloud_reg_graph),"Error: % " % graph.__class__
        feedbackset = []
        # TODO find the feedbackset
        cycles = nx.find_cycle(graph)
        for c in cycles:
            edge = c[0]
            if edge not in feedbackset:
                feedbackset.append(edge)
        self.feedbackset = feedbackset
        graph.remove_nodes_from(feedbackset)
        return feedbackset
        
    def balance(self, graph):
        '''
        step2 把无环图 balancize
        '''
        set1 = []
        # TODO find the cut
        graph.remove_nodes(set1)
        return set1