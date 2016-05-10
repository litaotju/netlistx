# -*- coding: utf-8 -*-
u'''直接运行本模块，输入一个路径，对该路径下的所有vm文件，提取其增广S图，然后生成matlab脚本。
   和部分扫描优化问题。
'''
import os
import sys
import json

import networkx as nx

from netlistx.log import logger
from netlistx.file_util import vm_files2
from netlistx.graph.circuitgraph import get_graph
from netlistx.graph.esgraph import ESGraph
from netlistx.scan.util import get_namegraph, upath_cycle, gen_m_script, run_matlab, read_solution

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
    solution_file = esgrh.name + "_ESGraph_ScanFDs.txt"   #matlab输出的解的文件名
    port = 12345 #Socket port for matlab

    namegraph = get_namegraph(esgrh)          #namegraph = nx.DiGraph()

    selfloop_nodes = [node for node in namegraph.nodes_iter() if namegraph.has_edge(node, node)]
    
    ##FOR_DEBUG
    ##保存不平衡路径和环的信息到json对象
    try:
        os.makedirs(os.path.join(opath, 'with-selfloop'))
        os.makedirs(os.path.join(opath, 'without-selfloop'))
    except WindowsError, e:
        print e
        pass
    try:
        nx.write_dot(namegraph, os.path.join(opath, 'with-selfloop',esgrh.name + ".dot"))
    except UnicodeDecodeError, e:
        print e
        pass

    namegraph.remove_nodes_from(selfloop_nodes)

    try:
        nx.write_dot(namegraph, os.path.join(opath, 'without-selfloop', esgrh.name + ".dot"))
    except UnicodeDecodeError, e:
        print e
        pass
        
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
    node2x = {node: "x(%d)"%index for index, node in enumerate(namegraph.nodes())}
    constraints = gen_constraints(cycles, unpaths, node2x)

    scan_fds = []
    if constraints:
        gen_m_script(constraints, node2x, solution_file, port, script_file)
        run_matlab(script_file, port)
        scan_fds = read_solution(os.path.join(opath, solution_file), node2x) + selfloop_nodes
    else:
        scan_fds = selfloop_nodes
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

import netlistx.cliapp as cliapp
class MainApp(cliapp.CliApp):

    def __init__(self, name = "partial_esgraph"):
        super(MainApp, self).__init__(name)

    def _process(self, vm):
        OPATH = os.path.join(self.path, "ESMatlab")
        self.setOpath(OPATH)
        graph = get_graph(vm)
        esgrh = ESGraph(graph)
        scan_fds = get_scan_fds(esgrh, self.opath)
        fobj = open( os.path.join(OPATH, esgrh.name + "_SCAN_FDs.txt"), 'w')
        fobj.write("\n".join(scan_fds))
        fobj.close()

if __name__ == "__main__":
    MainApp().run()