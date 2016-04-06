# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 13:16:27 2015

@author: litao
@e-mail:litaotju@qq.com
@license: Free

"""
import os
import networkx as nx
import matplotlib.pylab as plt

# user-defined module
import netlistx.circuit as cc
from netlistx.exception    import *
from netlistx.file_util    import vm_files

from crgraph      import CloudRegGraph
from circuitgraph import get_graph

class Ballaster:
    '''
        作用：把CloudRegGraph变成一个b结构，最终返回的值应该是原图中的regs节点
        注意ballaster当中的函数都对整数型的节点的图有效
    '''
    def __init__(self, graph):
        ''' para: graph, a CloudRegGraph instance
        '''
        # 9.25 修改构造函数
        assert isinstance(graph, nx.DiGraph), str(graph.__class__)
        self.graph = graph
        self.intgraph = nx.DiGraph( name = graph.name + "_intgraph")
        self.node_map = {}
        self.inv_node_map = {}
        self.__convert2intgraph()
        
    def __convert2intgraph(self):
        ''' 
            拓扑图只是包含了节点以及他们的连接，所以在进行基于结构的算法时候只需要
            把图转换成每一个节点是独特的整数的图就可以了,同时返回节点队列，
            用于算法找到整数边之后，get_scan_fd的查询
        '''
        nodes = self.graph.nodes()
        for i in range(0, len(nodes) ):
            self.node_map[i] = nodes[i]
            self.inv_node_map[ nodes[i] ] = i
        weight = nx.get_edge_attributes( self.graph, "weight" )
        if not weight:
            weight = {edge: 1 for edge in self.graph.edges_iter() }
        for edge in self.graph.edges_iter():
            intedge = (self.inv_node_map[edge[0]], self.inv_node_map[ edge[1] ] )
            self.intgraph.add_edge(intedge[0], intedge[1], {'weight': weight[edge],'label': weight[edge]})
        
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
            graph.fas.append( (self.node_map[index[0]], self.node_map[index[1]]) )
        # 只是在整数图上进行移除，所以下面的操作也只是针对整数图
        self.intgraph.remove_edges_from(feedbackset_index)  
        self.intgraph.fas = feedbackset_index
        if not feedbackset_index: print "Info: none FAS found in this graph"
        return feedbackset_index
        
    def balance(self,graph):
        '''parame: graph, a DAG its.__class__ == nx.DiGraph
           return: r,     removed edges set so makr the input graph a b-structure
        '''
        # step2 ,输入一个无环的图，对其进行balance
        # 只处理整数形式的图，每一个整数对应的节点可以在后面查到
        # 输入进来的图应该是连通的，如果存在非连通图，minimum_edge_cut就会产生问题
        assert nx.is_directed_acyclic_graph(graph),\
            "The target graph you want to banlance is not a DAG"
        r = [] # removed set
        if self.__check(graph):
            return r
        #非B-Stucture时，一直循环下去
        # BUGY: 如果cs为空呢，那么不可能有两个图返回来，这时候怎么办
        print "Cutting Graph"
        cs, g1, g2 = self.__cut(graph) 
        r = self.balance(g1) + self.balance(g2) + cs
        csl = []
        for eachEdge in cs:
            under_check_graph = graph.copy()
            under_check_graph.remove_edges_from(r)
            under_check_graph.add_edges_from(csl)
            under_check_graph.add_edge(eachEdge[0], eachEdge[1])
            if self.__check(under_check_graph):
                print "Edge: %s added back" % str(eachEdge)
                csl.append(eachEdge)
                graph.add_edge(eachEdge[0],eachEdge[1])
        for eachEdge in csl:
            r.remove(eachEdge)
        print "Removed Edge Set: %s" % str(r)
        return r

    #--------------------------------------------------------------------------------
    # 下面是直供balance算法调用的私有函数    
    def __check(self,graph):
        '''
        输入一个图G(v,A,H)来判断是否是B-structure,
        返回：True:是B-Structure，False，不是B-Structure
        '''
        # No hold register in this graph
        debug = False
        if debug: print "Procesing: checking graph for b-structure"
        if not isinstance(graph, nx.DiGraph):
            print "The graph is not a nx.DiGraph isinstance"
            raise Exception
        if not nx.is_directed_acyclic_graph(graph):
            return False
        roots = [node for node in graph.nodes_iter() if graph.in_degree()[node]==0]
        if len(roots) < 1:
            return False
        # 广度优先搜索,访问根节点，访问根节点的下一层节点， 为每一个点定Level
        # 访问一层节点的下一层节点，直到将所有的节点访问完，跳出。
        for root in roots:
            bfs_queue = [root]
            level = {root:0 }                  #记录每一个点的LEVEL的字典，初始只记录当前root
            been_levelized = []                #已经被定级的节点
            current_level = 0                  #当前的层
            if debug: print "root          :%s" % str(root)
            while(bfs_queue):
		        # 传进来的bfs_queque的层是已知的，
		        # 记录下它们的所有后继结点，并为他们定层次为n+1,同时放到待访问序列里面
                current_level +=1
                next_level_que = []
                for eachNode in bfs_queue:
                    for eachSucc in graph.successors(eachNode):
				        # 当一个节点是当前层多个节点的后继时，只加入到next_level_que一次
                        if not eachSucc in next_level_que:
                            next_level_que.append(eachSucc)
                            if debug: print "now: %s" % str(eachSucc)
                            if not level.has_key(eachSucc):
                                level[eachSucc] = current_level
                            elif level[eachSucc] ==current_level:
                                continue
                            else:
                                if debug: print "node: %s has violated the rule. %d,%d" \
							            % (str(eachSucc),level[eachSucc],current_level)
                                return False
                been_levelized += bfs_queue
                bfs_queue = next_level_que
                if debug:
                    print "been_levelized:%s " % str(been_levelized)+str(next_level_que)
                    print "root_queue    :%s " % str(next_level_que)
            if debug: print "Level: %s" % str(level)
        return True
    #--------------------------------------------------------------------------------
    
    def __cut(self, graph):
        ''' parame: 
                graph:a nx.DiGraph obj
	        return:
		        cs : edge cut set of the graph
		        g1 , g2 : subgraphs induced by cs
	
        '''
        debug = True
        assert isinstance(graph, nx.DiGraph), "Input_para.__class__  %s " % graph.__class__
        assert graph.number_of_nodes() > 1,   "Number of nodes: %d" % graph.number_of_nodes()
        if debug: print "Digraph Edges Are:\n    %s" % str(graph.edges())
        unigraph = nx.Graph(graph)           #将输入的图转为无向图
        cs = nx.minimum_edge_cut(unigraph)   #找出该无向图的minimum edge cut -> CS
        #balance函数调用cut前，graph一定是一个un-balance 结构，所以一定有CUT?
        if not cs:
            raise Exception,"Cut Set of this graph is Empty"
        #CS中的边，可能不存在于原来的有向图中，所以需要将这种边的方向颠倒
        #将所有real edge,存到RCS中
        rcs = []
        original_edges = graph.edges()
        for eachEdge in cs:
            if not eachEdge in original_edges:
                eachEdge = (eachEdge[1], eachEdge[0]) #调换方向
            rcs.append(eachEdge)
        graph.remove_edges_from(rcs)			      #在原图中移除CS
        if debug: print "Edge Cut Set RCS :\n    %s" % str(rcs)
        if debug: print "After remove RCS :\n    %s" % str(graph.edges())
    
        # 移除RCS中的边之后得到的两个Weakly Connected Subgraph
        glist = []
        for eachCntComp in nx.weakly_connected_component_subgraphs(graph):
		    #找到移除CS后的两个弱连接分量
            glist.append(eachCntComp)
            if debug:
                print "Weakly CC %d:" % len(glist)
                print "    nodes:%s" % eachCntComp.nodes() 
                print "    edges:%s" % eachCntComp.edges()
        assert len(glist) == 2
        return rcs, glist[0], glist[1]

    def get_scan_fd(self, scans):
        '''从边来获取要扫描的D触发器
            para：r
            return: scan_fds , a list of cc.circuit_module instance
        '''
        if not isinstance( self.graph, CloudRegGraph):
            print "Not a cloudRegGraph, has cannot get scanfd."
            return []
        scan_fds = []
        for eachEdge  in scans:
            source = self.node_map[eachEdge[0]]
            sink   = self.node_map[eachEdge[1]]
            scan_fds += self.arc[(source,sink)]
        return scan_fds



    
