# -*- coding: utf-8 -*-
import time
import os

import networkx as nx

import netlistx.circuit as cc
from netlistx.log import logger
from netlistx import CircuitGraph

__all__ = ["ESGraph"]

class ESGraph(nx.DiGraph):
    u"""增广S图类"""
    
    EDGE_ATTR_ISNEW_ADDED = 'is_new_added' #True or False
    
    def __init__(self, circuitgraph = None):
        '''@params: 
                circuitgraph: an instance of CircuitGraph class
        '''
        nx.DiGraph.__init__( self )  
        circuitgraph.topo_copy( self )
        self.name = circuitgraph.name
        comb_nodes = [node for node in self.nodes() if cc.isComb(node) ]
        
        # if Debug make these true
        self.__with_data = False #改变边的时候，带不带数据
        self.__check_comb_loops = False #是否检查组合逻辑环。默认不检查
        if self.__check_comb_loops:
            self.assert_no_comb_cycles()
        
        start = time.clock()
        for edge in self.edges_iter():
            self[edge[0]][edge[1]][ESGraph.EDGE_ATTR_ISNEW_ADDED] = False
        for node in comb_nodes:
            # 对一个组合节点操作之前，保证电路中没有这个组合节点的自环。
            if self.has_edge(node, node):
                msg = "Found combinational self-loop in node: %s" % node
                if self.__with_data:
                    msg += ("\n port_pairs:" + str(self[node][node][CircuitGraph.EDGE_ATTR_PORT_PAIRS]) )
                    msg += ("\n connections:" + str(self[node][node][CircuitGraph.EDGE_ATTR_PORT_PAIRS] ))
                logger.error(msg)
                logger.error("Does the original graph has this self loop? %s" % circuitgraph.has_edge(node, node) )
                self.remove_edge(node, node)
                #raise AssertionError, msg

            #获取node节点的前驱后后继，有可能有交集。
            pres = self.predecessors( node )
            succs = self.successors( node )

            #待加入的新边集合
            edges = []

            edges = [ (pre, succ ) for pre in pres for succ in succs ]
            for edge in edges:
                #如果发现将要加入组合逻辑自环，记录下错误，并跳过。不加入这个自环的边
                if (edge[0] is edge[1]) and cc.isComb(edge[0]):
                    logger.error("Found combinational loop in circuit")
                    logger.error( "cur node is:\n%s, anothoer loop node is:\n%s" % (node, edge[0]) )
                    logger.error("Is these edge new added: Cur->Succ:%s Succ->Cur:%s" % 
                                 (self[node][succ][ESGraph.EDGE_ATTR_ISNEW_ADDED], self[pre][node][ESGraph.EDGE_ATTR_ISNEW_ADDED]) 
                                 )
                    logger.error("But no self loop added, this edge is ignoreed")
                #否则，加入边。
                else:
                    self.add_edge(edge[0], edge[1], {ESGraph.EDGE_ATTR_ISNEW_ADDED: True} )
            
            ##旧的实现方式，有三层循环，所以太慢了，改为用列表推导的方式实现
            #for pre in pres:
            #    for succ in succs:
            #        if pre is node or succ is node:
            #            logger.warning("Found a combinational self-loop: %s" % node.name )
            #            continue
            #        ##但是原来边上的数据太多了，所以这部分特变慢。对于增广S图如果不重要，完全可以不要边上的数据
            #        ##保存原来的边上的数据
            #        if self.__with_data:
            #            port_pairs = self.get_edge_data(pre, node)[CircuitGraph.EDGE_ATTR_PORT_PAIRS]
            #            port_pairs += self.get_edge_data(node, succ)[CircuitGraph.EDGE_ATTR_PORT_PAIRS]

            #            connections = self.get_edge_data(pre, node)[CircuitGraph.EDGE_ATTR_CONNECTIONS]
            #            connections += self.get_edge_data(node, succ)[CircuitGraph.EDGE_ATTR_CONNECTIONS]
            #            data = { 
            #                     CircuitGraph.EDGE_ATTR_PORT_PAIRS: port_pairs,
            #                     CircuitGraph.EDGE_ATTR_CONNECTIONS: connections
            #                    }
            #            edges.append( (pre, succ, data) )
            #        else:
            #            edges.append( (pre, succ) )
            self.remove_node(node )
        #检查组合逻辑环
        if self.__check_comb_loops:
            self.assert_no_comb_cycles()
        #打印消耗的时间
        logger.debug("ESGraph init consumed time %d" % ( time.clock() - start ) ) 
        return

    def info(self):
        return os.linesep.join( ["-"*30,
                                 "Info of Extended S-Graph:",
                                  nx.info( self ),
                                 "Number of self-loops: %d" % self.number_of_selfloops(),
                                 "-"*30 ])
    
    INFO_ITEMS = ["timestamp", 'name', 'nodes', 'edges', 'self-loops','average-in-degree', 'average-out-degree', "time"]
    def info_items(self):
        u'''获取每一个信息的值
        '''
        nnodes = self.number_of_nodes()
        #顺序必须与INFO_ITEMS中的顺序对应
        items = [time.time(),
                self.name, 
                nnodes,
                self.number_of_edges(), 
                self.number_of_selfloops(), 
                sum(self.in_degree().values())/float(nnodes),
                sum(self.out_degree().values())/float(nnodes),
                time.ctime(), 
               ]
        return items

    def save_info_item2csv(self, filename, sep = ', '):
        u'''向 csv文件中加入一个条目，方便做数据统计
        '''
        try:
            if not os.path.exists(filename):
                #如果没有这个文件，打开并且添加第一行
                f = open(filename, 'w')
                f.write( sep.join(ESGraph.INFO_ITEMS)+ os.linesep )
            else:
                f = open(filename, 'a')
        except IOError, e:
            logger.error("Cannot open file %s" % e)
            return
        #没有异常，就直接写入record
        else:
            f.write( sep.join( ["%s" % i for i in self.info_items()] ) + os.linesep)
            f.close()
        return

    def assert_no_comb_cycles(self ):
        u'''确保图中的每一个环上面，至少存在一个节点 __is_dff(node)返回True
        '''
        #强制类型转换
        #Note: 由于simple_cycles中调用了 type(self)( self.edges_iter() )
        #      这里 type(self)() == ESGraph.__init__()
        #      相当于把  self.edges_iter() 返回的生成器，传递给ESGraph的构造函数。而ESGraph的构造函数需要唯一的参数， circuitgraph
        #      所以系统认为， self.edges_iter()这个生成器就是 circuitgraph. 自然会去调用构造函数中的 circuitgraph.topy()拷贝
        #      主要原因的 nx.simple_cycles() 默认可以接受 nx.DiGraph对象，但是接受它的子类的对象是有问题的
        #      所以在进行判断时，应该将 self强制转换为 nx.DiGraph对象，传递给nx.simple_cycles()
        for cycle in nx.simple_cycles( nx.DiGraph(self) ):
            has_dff_in_cycle = False
            for node in cycle:
                if cc.isDff(node):
                    has_dff_in_cycle = True
                    break
            if not has_dff_in_cycle:
                logger.error( "Assertion Error: has pure combinational cycle")
                logger.error( (" "*4).join( [node.name for node in cycle] )  )
                raise AssertionError
        return
