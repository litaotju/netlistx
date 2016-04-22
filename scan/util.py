# -*-coding:utf-8 -*- #
import re
import os
import sys
import copy
import time
import socket

import networkx as nx

import netlistx.circuit as cc
from netlistx.log import logger
from netlistx.prototype.unbpath import unbalance_paths

def get_namegraph( graph ):
    u'''
        @brief:
            复制原图的拓扑结构，生成一个字符串为节点的图，每一个节点的字符串对应着原图的节点名
        @param:
            graph, a graph whose node is either a cc.port() or an obj with a name attr
        return:
            返回和同等拓扑结构的图. 新图的节点是原图的节点的名称,为字符串类型变量.
    '''
    get_name = lambda node : node.name if not cc.isPort(node) else node.port_assign.string
    tmp = {}
    for node in graph.nodes_iter():
        unique_name = get_name(node)
        assert not tmp.has_key(unique_name), \
            "Node:%s, has the same name with:%s, name:%s" % (node, tmp[node.name], unique_name )
        tmp[unique_name] = node

    namegraph = nx.DiGraph()
    namegraph.add_nodes_from(tmp.iterkeys())
    namegraph.add_edges_from(((edge[0].name, edge[1].name) for edge in graph.edges()))
    logger.debug("get name graph successfully")
    return namegraph

def upath_cycle(namegraph):
    u'''@ brief: 
            找出图中所有的不平衡路径和环
        @ param: 
            namegraph, a nx.DiGraph obj
        @ return: 
            (upaths, cycles) : 图中所有的不平衡路径和环
    '''       
    upaths = unbalance_paths(namegraph)
    logger.debug("get unblance path succesefully")
    cycles = []
    for cycle in nx.simple_cycles(namegraph):
        cycles.append(cycle)
    logger.debug("get cycles succesefully")
    return upaths, cycles

def read_solution(solutionfile, entity2x):
    u'''@brief:
            读取matlab的计算结果，得到需要变为扫描的边
        @params:
            sulutionfile:  文件名，每一行的形式为  x\([\d]+\) [01]
            entity2x: 字典， { entity(任何实体): x\(\[\d]+\) }
        @return:
            list, 每一个 变量x%d==0 对应的的实体组成的队列
    '''
    ret = []
    x2entity = { x: entity for entity, x in entity2x.iteritems() }
    with open(solutionfile,'r') as solution:
        for line in solution:
            if line.startswith("//"): continue
            (x, val) = tuple( line.strip().split() ) 
            if int(val) == 0:
                ret.append( x2entity[x] )
    return ret
