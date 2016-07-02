# -*- coding: utf-8 -*-
u'''本模块实现了一个使用增广S图的优化方法来进行部分扫描触发器的方法。
以及实现了ESScanApp类,作为命令行应用程序。
'''
import os
import json
import time
import networkx as nx

import netlistx.circuit as cc
from netlistx.log import logger
from netlistx.file_util import StdOutRedirect
from netlistx.graph.util import WriteDotBeforeAfter
from netlistx.graph.circuitgraph import CircuitGraph
from netlistx.graph.esgraph import ESGraph
from netlistx.scan.util import get_namegraph, upath_cycle, gen_m_script, run_matlab, read_solution, isbalanced
from netlistx.scan.scanapp import ScanApp

#是否保存中间信息
INTERMEDIATE = True

#UNP约束生成方法选择
SIMPLE = 1  
COMPLEX = 2
STUPID = 3
MERGE_GROUP = 4
PARTIAL_MERGE_GROUP = 5
#生成UNP约束的级别，可在1,2,3,4,5中选一个
LEVEL = 1

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
    # 保存esgrh的条目到opath路径下，方便多次实验数据的比较
    namegraph = get_namegraph(esgrh)  # namegraph = nx.DiGraph()
    selfloop_nodes = [node for node in namegraph.nodes_iter()
                      if namegraph.has_edge(node, node)]
    namegraph.name = esgrh.name
    with WriteDotBeforeAfter(opath, "remove-selfloop", namegraph):
        namegraph.remove_nodes_from(selfloop_nodes)

    unpaths, cycles = upath_cycle(namegraph)  # unpaths = [], cycles = []
    # {name: x%d}
    node2x = {node: "x(%d)" % (index + 1)
              for index, node in enumerate(namegraph.nodes())}
    constraints = gen_constraints(cycles, unpaths, node2x)
    
    ##检查中间结果用
    if INTERMEDIATE:
        # 保存不平衡路径和环的信息到json对象
        upath_json = open(os.path.join(opath, esgrh.name + "_upath.json"), 'w')
        cycle_json = open(os.path.join(opath, esgrh.name + "_cycle.json"), 'w')
        json.dump({("%s->%s" % (key[0], key[1])): value for key, value in unpaths.iteritems()},
                  upath_json,
                  indent=4)
        json.dump(cycles, cycle_json, indent=4)
        upath_json.close()
        cycle_json.close()
        # 保存节点-x的映射关系
        node2x_json = open(os.path.join(opath, esgrh.name + "_node2x.json"), 'w')
        json.dump(node2x, node2x_json, indent=4)
        node2x_json.close()
    
    #保存UNP个数，自环个数等信息
    f = os.path.join(opath, "constraints_records.csv")
    if not os.path.exists(f):
        with open(f, 'w') as fobj:
            fobj.write("TimeStamp, time, circuit, #UNP, #Cycle, #self-loop, #constraints\n")
    with open(f, 'a') as fobj:
        fobj.write("%s,%s,%s, %d, %d, %d, %d\n" % (time.ctime(), time.time(),\
            esgrh.name, len(unpaths), len(cycles), len(selfloop_nodes), len(constraints)))
    
    scan_fds = selfloop_nodes
    script_file = os.path.join(opath, esgrh.name + ".m")  # 输出的matlab脚本文件名，如果需要的话
    solution_file = esgrh.name + "_ESGraph_MatSolution.txt"  # matlab输出的解的文件名
    port = 12345  # Socket port for matlab
    if constraints:
        obj = ""
        ## UNP之间的Paths没有合并的情况时
        if not LEVEL in [MERGE_GROUP,PARTIAL_MERGE_GROUP]:
            weight = {}
            MAX_NODE = len(node2x) + 1000
            for entity, x in node2x.iteritems():
                # 触发器节点的权重设置为1
                if(cc.isDff(namegraph.original_node[entity])):
                    weight[x] = 1
                else:
                    #设置端口的权重极大，使得尽可能选择触发器
                    assert(cc.isPort(namegraph.original_node[entity]))
                    weight[x] = MAX_NODE
            weights = []
            for i in range(0, len(node2x)):
                _ = "x(%d)" %(i+1)
                weights.append(weight[_])
            obj = "W = %s;\n" % weights
            obj += "obj = -x*W';\n"
        ## UNP之间的Paths会有合并的情况
        else:
            weight = []
            x2entities = {}
            for entity, x in node2x.iteritems():
                if not x2entities.has_key(x):
                    x2entities[x] = []
                x2entities[x].append(entity)
            for i in range(0, len(node2x)):
                _ = "x(%d)"%(i+1)
                if x2entities.has_key(_):
                    weight.append(len(x2entities[_]))
                else:
                    weight.append(1)
            obj = "W = %s;\n" % weight
            obj += "obj = -x*W';\n";
        gen_m_script(obj,constraints,len(node2x),solution_file,port,script_file)
        if LEVEL == 1:
            run_matlab(script_file, port)
            scan_fds += read_solution(os.path.join(opath, solution_file), node2x)
    
    #从字符串，获取真正的扫描触发器对象，
    scan_fds = [namegraph.original_node[name] for name in scan_fds]
    esgrh.remove_nodes_from(scan_fds)

    # 解里面可能有端口。保存解中的端口
    scan_ports = filter(cc.isPort, scan_fds)
    if scan_ports:
        with StdOutRedirect(os.path.join(opath, "ScanPorts_%s.txt" % esgrh.name)):
            for port in scan_ports:
                print(port.port_type + ":" + port.name)
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
    # 获取环的约束
    cycle_constaints = []
    for cycle in cycles:
        if len(cycle) == 1:
            continue
        variables = [node2x[node] for node in cycle]
        cycle_constaints.append("+".join(variables) +
                                "<= %d;..." % (len(variables) - 1))
    unpath_constraints = funcs_to_generate_unp_const[LEVEL](unpaths, node2x)
    return cycle_constaints + unpath_constraints


def upaths_contraints_simple(unpaths, node2x):
    u'''每一个UNP，只考虑起点和终点
    '''
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
        unpath_constraints.append(e)
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

from netlistx.scan.unpaths_constraints import *
#级别： 产生UNP约束的函数
funcs_to_generate_unp_const = {
    SIMPLE: upaths_contraints_simple, # x_start + x_end <= 1
    COMPLEX: upaths_contraints_complex, # 看UNP是否和其他UNP之间有交集
    STUPID: upaths_contraints_stupid,   #分组 blabla..
    MERGE_GROUP: upaths_contraints_more_complex, # 看Group是否和其他Group有交集
    PARTIAL_MERGE_GROUP: upaths_contraints_moremore_complex  #看Path是否和其他Path有交集
    }

class ESScanApp(ScanApp):

    def __init__(self, name="ESScan"):
        super(ESScanApp, self).__init__(name)

    def _get_scan_fds(self):
        graph = CircuitGraph(self.netlist)
        esgrh = ESGraph(graph)
        esgrh.save_info_item2csv(os.path.join(self.opath, "esgrh_records.csv"))
        self.fds = filter(cc.isDff, graph.nodes_iter())
        self.scan_fds = get_scan_fds(esgrh, self.opath)
        esgrh.remove_nodes_from(self.scan_fds)
        assert(isbalanced(esgrh))

if __name__ == "__main__":
    app = ESScanApp()
    def get_level():
        level = int(raw_input("set level:"))
        if level < 1 or level > 5:
            level = 1
        LEVEL = level
    app.addFunction("level", get_level)
    app.run()
