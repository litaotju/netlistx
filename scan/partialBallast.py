# -*- coding: utf-8 -*-

import time
import os
import networkx as nx

# user-defined module
import netlistx.circuit as cc

from netlistx.graph.cloudgraph import CloudRegGraph
from netlistx.graph.circuitgraph import CircuitGraph
from netlistx.prototype.fas import comb_fas
from netlistx.scan.scanapp import ScanApp
from netlistx.scan.instrumentor import FullReplaceInstrumentor

from netlistx.scan.util import isbalanced, RecordRuntime
__check = isbalanced

__all__ = ["balance", "ballast", "BallastApp"]


def balance(graph):
    assert nx.is_directed_acyclic_graph(graph),\
        "The target graph you want to banlance is not a DAG"
    r = []  # removed set
    if __check(graph):
        return r
    weight = nx.get_edge_attributes(graph, 'weight')
    assert len(weight) == graph.number_of_edges()
    cs, g1, g2 = __cut(graph)
    r = balance(g1) + balance(g2) + cs
    csl = []
    cs.sort(key=lambda x: weight[x], reverse=True)
    for i in range(0, len(cs)):
        eachEdge = cs[i]
        under_check_graph = graph.copy()
        under_check_graph.remove_edges_from(r)
        under_check_graph.add_edges_from(csl)
        under_check_graph.add_edge(eachEdge[0], eachEdge[1])
        if __check(under_check_graph):
            csl.append(eachEdge)
            graph.add_edge(eachEdge[0], eachEdge[1], {'weight': weight[eachEdge]})
    for eachEdge in csl:
        r.remove(eachEdge)
    return r


def __cut(graph):
    u''' param: 
            graph:a nx.DiGraph obj
            return:
                    cs : edge cut set of the graph
                    g1 , g2 : subgraphs induced by cs

    '''
    assert isinstance(graph, nx.DiGraph), "graph class: %s " % graph.__class__
    assert graph.number_of_nodes() > 1, "Number of nodes: %d" % graph.number_of_nodes()
    unigraph = nx.Graph(graph)
    cs = nx.minimum_edge_cut(unigraph)
    if not cs:
        raise Exception, "Cut Set of this graph is Empty"

    # CS中的边，可能不存在于原来的有向图中，所以需要将这种边的方向颠倒
    # 将所有real edge,存到RCS中
    rcs = []
    for eachEdge in cs:
        if not graph.has_edge(eachEdge[0], eachEdge[1]):
            eachEdge = (eachEdge[1], eachEdge[0])  # 调换方向
        rcs.append(eachEdge)
    graph.remove_edges_from(rcs)
    glist = []
    for eachCntComp in nx.weakly_connected_component_subgraphs(graph, copy=False):
        glist.append(eachCntComp)
    assert len(glist) == 2
    return rcs, glist[0], glist[1]


def convert2int(graph):
    u'''把传进来的图转化为整数图
    '''
    intgraph = nx.DiGraph(name=graph.name + "_intgraph")
    node2i = {}
    invmap = {}
    i = 0
    for node in graph.nodes_iter():
        node2i[node] = i
        invmap[i] = node
        i += 1
    oweight = nx.get_edge_attributes(graph, 'weight')
    for edge in graph.edges_iter():
        intedge = (node2i[edge[0]], node2i[edge[1]])
        intgraph.add_edge(intedge[0], intedge[1], weight=oweight[edge])
    return intgraph, invmap


def ballast(crgraph):
    u'''Ballast方法的完整实现
    '''
    intgraph, invmap = convert2int(crgraph)
    comfas = []
    r = []

    timecycle = 0
    timebal = 0

    for subgraph in nx.weakly_connected_component_subgraphs(intgraph):
        start = time.clock()
        comfas += comb_fas(subgraph)
        tcycle = time.clock()

        r += balance(subgraph)
        tbal = time.clock()

        timecycle += (tcycle - start)
        timebal += (tbal - tcycle)
    fobj = open(os.path.join("test","timeStats.txt"), 'a')
    fobj.write("%s , cycle:%.3f, bal:%.3f, total:%.3f\n"
               % (crgraph.name[:-11], timecycle, timebal, (timecycle + timebal)))
    fobj.close()

    # print "CombFAS:", comfas
    # print "R:", r
    if not r:
        print "Info: %s is blance after cycle removed" % crgraph.name
    else:
        print "Info: %d edges removed in unblanced paths." % len(r)
    scanfds = []
    for edge in comfas + r:
        realedge = invmap[edge[0]], invmap[edge[1]]
        scanfds += crgraph.arcs[realedge]
    return scanfds


class BallastApp(ScanApp):
    u'''可直接运行此App，获得Ballast方法的扫描触发器
    '''

    def __init__(self, name="Ballast"):
        super(BallastApp, self).__init__(name)

    def _get_scan_fds(self):
        g = CircuitGraph(self.netlist)
        g.info()
        cr = CloudRegGraph(g)
        cr.info()
        self.fds = filter(cc.isDff, g.nodes_iter())
        with RecordRuntime( os.path.join(self.opath, "runtime.txt"), g.name): 
            self.scan_fds = ballast(cr)

    def after_get_scan_fds(self):

        # 插入扫描后的输出子路径
        INSERT_PATH = "netlist_inserted"
        # 插入扫描后的输出子路径
        BEFORE_INSERT_PATH = "netlist"

        # 保存插入前的网表
        opath = os.path.join(self.opath, BEFORE_INSERT_PATH)
        if not os.path.exists(opath):
            os.makedirs(opath)
        self.netlist.write(opath)

        # 如果子类没有指定指定instumentor，则指定默认的instrumentor
        # 否则使用子类指定的instrumentor 进行扫描插入
        instrumentor = FullReplaceInstrumentor(self.netlist, self.scan_fds)
        instrumentor.insert_scan()
        # 保存插入后的网表
        opath = os.path.join(self.opath, INSERT_PATH)
        if not os.path.exists(opath):
            os.makedirs(opath)
        self.netlist.write(opath)

if __name__ == "__main__":
    BallastApp().run()
