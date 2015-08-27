# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 13:16:27 2015

@author: litao
@e-mail:litaotju@qq.com
@license: Free

"""
import networkx as nx
import class_circuit as cc
from crgraph import CloudRegGraph


class Ballaster:
    '''
        作用：把CloudRegGraph变成一个b结构，最终返回的值应该是原图中的regs节点
        注意ballaster当中的函数都对整数型的节点的图有效
    '''
    def __init__(self, graph):
        self.graph = graph #将一个cloud_reg绑定到self上   
        self.intgraph , self.node_mapping = self.__convert2intgraph()
        if isinstance(graph, CloudRegGraph):
            self.arc = self.__reg2arc()   #把FD全变成边,每一个FD为key,(precs,succs)为值的dict
        elif not isinstance(graph , nx.DiGraph):
            print "Ballaster Error : input graph is an CloudRegGraph"
            print "                  but an instance of %s " % str(graph.__class__)
            raise SystemExit()
    
    def __reg2arc(self):
        '''把所有的reg节点 ignore掉，将其前后相连'''
        graph = self.graph
        arc = {}       
        for reg in graph.regs:
            precs = graph.predecessors(reg)
            succs = graph.successors(reg)
            graph.remove_node(reg)
            if len(precs) == 1 : # must be 1, if __check_rules succsfull
                assert isinstance(precs[0], nx.DiGraph),\
                    "reg %s %s -->> succ %s %s" % \
                    (reg.cellref, reg.name, precs[0].cellref, precs[0].name)
            else:
                # 没有前驱结点的FD将不会保留边的信息
                continue
            if len(succs) == 1 :
                assert isinstance(succ[0], nx.DiGraph) ,\
                    "reg %s %s -->> succ %s %s" % \
                    (reg.cellref, reg.name, succ[0].cellref, succ[0].name)
                graph.add_edge(prec[0], succ[0])
            arc[reg]=(precs, succs)
        return arc

    def __convert2intgraph(self):
        ''' 
            拓扑图只是包含了节点以及他们的连接，所以在进行基于结构的算法时候只需要
            把图转换成每一个节点是独特的整数的图就可以了。
            同时返回每一个整数所对应的原图节点对象
        '''
        graph = self.graph
        intgraph = nx.DiGraph()
        nodes = graph.nodes()
        for edge in graph.edges_iter():
            intedge = (nodes.index(edge[0]), nodes.index(edge[1]))
            intgraph.add_edge(intedge[0], intedge[1])
        return intgraph, nodes
        
    def feedbackset(self):
        '''
        step1 找出给定的 cr 图的 feedback 集合,存到数据self.graph.fas 当中去
        '''
        graph = self.graph
        graph.fas = []
        feedbackset_index = []
        for c in nx.simple_cycles(self.intgraph):
            print "Info: find cycle %s " % c
            if len(c) == 1: 
            #self-loop
                edge = (c[0], c[0])
            else:
                edge = (c[0], c[1])
            if not edge in feedbackset_index: # 因为edge是一个整数型元组，所以这是对的
                feedbackset_index.append(edge)
        for index in feedbackset_index:
            graph.fas.append( (self.node_mapping[index[0]], self.node_mapping[index[1]]) )
        self.intgraph.remove_edges_from(feedbackset_index)
        return None
        
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
    
    
#------------------------------------------------------------------------------    
if __name__ == '__main__':
    'test the ballaster'    
    
    g1 = nx.DiGraph()
    g1.add_path([0,1,2,0])
    g1.add_path([2,3,4,2])
    b1 = Ballaster(g1)
    b1.feedbackset()
    print g1.fas
    g2 = nx.DiGraph()
    g2.add_path([1,0,5,1])
    g2.add_path([5,1,3,5])
    g2.add_path([2,1,3,2])
    g2.add_path([5,4,3,5])
    b2 = Ballaster(g2)
    b2.feedbackset()
    print g2.fas
    