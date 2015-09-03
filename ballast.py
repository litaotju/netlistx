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
from exception import *

class Ballaster:
    '''
        作用：把CloudRegGraph变成一个b结构，最终返回的值应该是原图中的regs节点
        注意ballaster当中的函数都对整数型的节点的图有效
    '''
    def __init__(self, graph):
        self.graph = graph #将一个cloud_reg绑定到self上   
        if isinstance(graph, CloudRegGraph):
            # 新增的边 对应那些FDs,需要作为字典的值存储下来
            self.arc = self.__reg2arc()
            print "After __reg2arc:"
            print nx.info(self.graph)
        elif not isinstance(graph, nx.DiGraph):
            print "Ballaster Error : input graph is not an nx.DiGraph"
            print "                  but an instance of %s " % str(graph.__class__)
            raise BallastError
        # 注意整数图所存储的每一个节点都是Cloud, 没有Reg. Reg是以边的形式存在的
        self.intgraph , self.node_mapping = self.__convert2intgraph()
    
    def __reg2arc(self):
        '''把所有的reg节点 ignore掉，将其前后相连
        '''
        graph = self.graph
        arc = {} # 记录下来每一个由FD转换成的边，以及对应的FDs
        for reg in graph.regs:
            precs = graph.predecessors(reg)
            succs = graph.successors(reg)
            prec = None
            succ = None
            graph.remove_node(reg)
            if len(precs) == 1 : # must be 1, if __check_rules succsfull
                assert isinstance(precs[0], nx.DiGraph),\
                    "reg %s %s -->> prec %s %s" % \
                    (reg.cellref, reg.name, precs[0].cellref, precs[0].name)
                prec = precs[0]
            if len(succs) == 1 :
                assert isinstance(succs[0], nx.DiGraph) ,\
                    "reg %s %s -->> succ %s %s" % \
                    (reg.cellref, reg.name, succs[0].cellref, succs[0].name)
                succ = succs[0]
                if prec: #只有两个都非空的情况下，才新加入边
                    graph.add_edge(prec, succ)
            # 记录下来每一条边所对对应的多个FD，将它们组成一个队列作为一个字典的值，存储起来
            # （None,succ）表示这个点没有前驱只有后继
            # （prec,None）表示这个点没有后继只有前驱
            if not arc.has_key( (prec, succ) ):
                arc[(prec, succ)]= []
            arc[(prec, succ)].append(reg)
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
        node_mapping = nodes #每一个整数对应的FD,存储在这个列表当中
        return intgraph, node_mapping
        
    def feedbackset(self):
        '''
        step1 找出给定的 cr 图的 feedback 集合,存到数据self.graph.fas 当中去
        '''
        graph = self.graph
        graph.fas = [] # 给原图增加数据属性，fas
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
        # 只是在整数图上进行移除，所以下面的操作也只是针对整数图
        self.intgraph.remove_edges_from(feedbackset_index)  
        self.intgraph.fas = feedbackset_index
        return None
        
    def balance(self,intgraph):
        '''
        step2 把无环图 balancize
        '''
        #TODO balance
        #只处理整数形式的图，每一个整数对应的节点可以在后面查到
        assert nx.is_directed_acyclic_graph(intgraph),\
            "The target graph you want to banlance is not a DAG"
        r = [] # removed set
        while( not self.check(intgraph) ):
            #非B-Stucture时，一直循环下去
            cs = nx.minimum_edge_cut(intgraph)
            #TODO find the cut
            intgraph.remove_edges_from(cs)
            g1,g2 = find_connected_subgraph(intgraph)
            r = self.balance(g1)+self.balance(g2)+cs
            return set1
        return r
        
    def check(self, graph):
        '''
        输入一个图G(v,A,H)来判断是否是B-structure,
        返回：True:是B-Structure，False，不是B-Structure
        '''
        # No hold register in this graph
        if not isinstance(graph, nx.DiGraph):
            print "The graph is not a nx.DiGraph isinstance"
            #raise BallastError
            raise exception
        if not nx.is_directed_acyclic_graph(graph):
            return False
        roots = [node for node in graph.nodes_iter() if graph.in_degree()[node]==0]
        if len(roots) < 1:
            return False
        # 广度优先搜索,访问根节点，访问根节点的下一层节点，
        # 访问一层节点的下一层节点，直到将所有的节点访问完，
        # 跳出。注意死循环的情况，如一个环的话，自己就是自己的successors
        # 为每一个点定Level
        for root in roots:
            bfs_queue = [root]
            level = {root:0 }                  #记录每一个点的LEVEL的字典，初始只记录root
            been_levelized = []                #已经被定级的节点
            current_level = 0                  #当前的层
            print "root         :%s" % str(bfs_queue)
            while(1):
                # 传进来的bfs_queque的层是已知的，
                # 记录下它们的所有后继结点，并为他们定层次为n+1,同时放到待访问序列里面
                if len(bfs_queue) == 0:
                    break
                current_level +=1
                next_level_que = []
                for eachNode in bfs_queue:
                    for eachSucc in graph.successors(eachNode):
                        # 当一个节点是当前层多个节点的后继时，只加入到next_level_que一次
                        if not eachSucc in next_level_que:
                            next_level_que.append(eachSucc)
                            print "now:%d" % eachSucc
                            if not level.has_key(eachSucc):
                                level[eachSucc] = current_level
                            elif level[eachSucc] ==current_level:
                                continue
                            else:
                                print "node: %s has violated the rule. %d,%d" \
                                    % (str(eachSucc),level[eachSucc],current_level)
                                return False
                been_levelized += bfs_queue
                bfs_queue = next_level_que
                print "been_levelized:%s " % str(been_levelized)+str(next_level_que)
                print "root_queue    :%s " % str(next_level_que)
            print str(level)
        return True

    def find_connnected_subgraph(self, graph):
        pass

def __test_with_intgraph():
    '''使用整数图来测试Ballaster的算法
    '''
    g1 = nx.DiGraph()
    g1.add_path([0,1,2,0])
    g1.add_path([2,3,4,2])
    b1 = Ballaster(g1)
    b1.feedbackset()
    print "FAS is %s" % g1.fas
    g2 = nx.DiGraph()
    g2.add_path([1,0,5,1])
    g2.add_path([5,1,3,5])
    g2.add_path([2,1,3,2])
    g2.add_path([5,4,3,5])
    b2 = Ballaster(g2)
    b2.feedbackset()
    b2.balance()
    print "FAS is %s" % g2.fas

def __test_with_crgraph():
    from circuitgraph import get_graph_from_raw_input
    g = get_graph_from_raw_input()
    g.info()
    crgraph = CloudRegGraph(g)
    crgraph.info()
    ballast1 = Ballaster(crgraph)
    ballast1.feedbackset()
    print "Ballaster.intgraph.fas is:"
    print ballast1.intgraph.fas
    print nx.info(ballast1.intgraph)


#------------------------------------------------------------------------------    
if __name__ == '__main__':
    'test the ballaster'    
    #__test_with_intgraph()
    __test_with_crgraph()

    