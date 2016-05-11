# -*- coding: utf-8 -*-
u'''本模块实现了一个使用增广S图的优化方法来进行部分扫描触发器的方法。
以及实现了ESScanApp类,作为命令行应用程序。
'''
import os
import sys
import json

import networkx as nx

import netlistx.circuit as cc
from netlistx.log import logger
from netlistx.file_util import vm_files2
from netlistx.graph.circuitgraph import get_graph
from netlistx.graph.esgraph import ESGraph
from netlistx.scan.util import get_namegraph, upath_cycle, gen_m_script, run_matlab, read_solution
from netlistx.scan.scanapp import ScanApp

__all__ = ["ESScanApp"]

def get_scan_fds(esgrh, opath):
    u'''
        @brief：输入一个ESGraph对象 esgrh，和一个路径，在该路径下生成此esgrh的优化问题matlab脚本并求解。
        @params:
            esgrh: an ESGraph obj
            opath: an existing path to store the inter temp file
        @return:
            scan_fds [], a list of scan fds in esgrh
    '''
    assert isinstance(esgrh, ESGraph)
    script_file = os.path.join(opath, esgrh.name + ".m")  #输出的matlab脚本文件名，如果需要的话
    solution_file = esgrh.name + "_ESGraph_MatSolution.txt"   #matlab输出的解的文件名
    port = 12345 #Socket port for matlab

    namegraph = get_namegraph(esgrh)          #namegraph = nx.DiGraph()

    selfloop_nodes = [node for node in namegraph.nodes_iter() if namegraph.has_edge(node, node)]
    
    ##FOR_DEBUG
    ##保存不平衡路径和环的信息到json对象
    with_selfloop = os.path.join(opath, 'with-selfloop')
    without_selfloop = os.path.join(opath, 'without-selfloop')
    if not os.path.exists(with_selfloop):
        os.makedirs(with_selfloop)
    if not os.path.exists(without_selfloop):
        os.makedirs(without_selfloop)
    try:
        nx.write_dot(namegraph, os.path.join(with_selfloop, esgrh.name + ".dot"))
    except Exception, e:
        print e

    namegraph.remove_nodes_from(selfloop_nodes)

    try:
        nx.write_dot(namegraph, os.path.join(without_selfloop, esgrh.name + ".dot"))
    except Exception, e:
        print e
        
    unpaths, cycles = upath_cycle(namegraph)  #unpaths = [], cycles = []

    #upath_json = open(os.path.join(opath, esgrh.name + "_upath.json"), 'w')
    #cycle_json = open(os.path.join(opath, esgrh.name + "_cycle.json"), 'w')
    #json.dump({("%s->%s" % (key[0], key[1])): value for key,value in unpaths.iteritems()}, 
    #          upath_json, 
    #          indent=4,
    #          separators=(",",":"))
    #json.dump(cycles, cycle_json, indent=4)
    #upath_json.close()
    #cycle_json.close()

    fobj = open(os.path.join(opath, esgrh.name + "_upath.txt"), 'w')
    esgrh.save_info_item2csv(os.path.join(opath, "esgrh_records.csv"))
    fobj.write("ESGraph:%s has %d UNPs, %d cycles, %d self-loops" % \
                    (esgrh.name, len(unpaths), len(cycles), len(selfloop_nodes)))
    fobj.close()

    # {name: x%d}
    node2x = {node: "x(%d)" % (index+1) for index, node in enumerate(namegraph.nodes())}
    #node2x持久化，方便将运行matlab和读取solution分开
    node2x_json = open(os.path.join(opath, esgrh.name + "_node2x.json"), 'w')
    json.dump(node2x, node2x_json, indent=4)
    node2x_json.close()

    constraints = gen_constraints(cycles, unpaths, node2x)

    scan_fds = []
    if constraints:
        gen_m_script("-sum(x)", constraints, len(node2x), solution_file, port, script_file)
        run_matlab(script_file, port)
        scan_fds = read_solution(os.path.join(opath, solution_file), node2x) + selfloop_nodes
    else:
        scan_fds = selfloop_nodes
    ##TODO: 如果解里面有端口呢？
    scan_fds = [namegraph.original_node[name] for name in scan_fds]
    scan_fds = filter(cc.isDff, scan_fds)
    return scan_fds

def gen_constraints(cycles, unpaths, node2x):
    u'''
        @brief:
            输入环和不平衡路径，输出约束列表，每一个约束都是一个已 ;... 结尾的不等式 字符串
        @params:
            cycles: a list of simple cycles 
            unpaths: a dict {(source, target):[list of all unblanced paths between source->target]}
            node2x: a dict {node: x(%d)}
        @return:
            [] list of contraints
    '''
    #获取环的约束
    cycle_constaints = []
    for cycle in cycles:
        if len(cycle) == 1:
            continue
        variables = [node2x[node] for node in cycle]
        cycle_constaints.append("+".join(variables) + "<= %d;..." % (len(variables)-1))
    
    #获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        e = "%s+%s <= 1;..." %(node2x[source], node2x[target])
        unpath_constraints.append(e)

    logger.critical("ESGraph generated %d matlab upath constraints" % len(unpath_constraints))
    return cycle_constaints + unpath_constraints


class ESScanApp(ScanApp):

    def __init__(self, name="ESScan"):
        super(ESScanApp, self).__init__(name)

    def _get_scan_fds(self, vm):        
        graph = get_graph(vm)
        esgrh = ESGraph(graph)
        self.fds = filter(cc.isDff, graph.nodes_iter())
        self.scan_fds = get_scan_fds(esgrh, self.opath)

if __name__ == "__main__":
    ESScanApp().run()
