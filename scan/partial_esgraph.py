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
from netlistx.graph.circuitgraph import get_graph
from netlistx.graph.esgraph import ESGraph
from netlistx.scan.util import get_namegraph, upath_cycle, gen_m_script, run_matlab, read_solution, isbalanced
from netlistx.scan.scanapp import ScanApp

__all__ = ["ESScanApp"]

INTERMEDIATE = True #是否保存中间信息

SIMPLE = 1  #采用简单的不平衡路径约束生成，还是复杂的
COMPLEX = 2
STUPID = 3
LEVEL = SIMPLE 

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
        gen_m_script("-sum(x)", constraints, len(node2x),
                     solution_file, port, script_file)
        run_matlab(script_file, port)
        scan_fds += read_solution(os.path.join(opath, solution_file), node2x)
    scan_fds = [namegraph.original_node[name] for name in scan_fds]
    
    ##TODO:处理解当中的Port
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
    if LEVEL == COMPLEX:
        unpath_constraints = upaths_contraints_complex(unpaths, node2x)
    elif LEVEL == STUPID:
        unpath_constraints = upaths_contraints_stupid(unpaths, node2x)
    else: #其他任何情况都认为使用 
        unpath_constraints = upaths_contraints_simple(unpaths, node2x)
    return cycle_constaints + unpath_constraints


def upaths_contraints_simple(unpaths, node2x):
    u'''简单的求约束的方法
    '''
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        e = "%s+%s <= 1;..." % (node2x[source], node2x[target])
        unpath_constraints.append(e)
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints


def upaths_contraints_complex(unpaths, node2x):
    u'''复杂的求约束的方法
    '''
    unpath_constraints = []
    upaths_set = {}
    for (source, target), paths_between in unpaths.iteritems():
        temp_set = reduce(lambda x, y: x.union(set(y)), paths_between, set())
        upaths_set[(source, target)] = temp_set

    upaths_has_common = {}
    for (source, target), temp_set in upaths_set.iteritems():
        has_common = False
        for (source1, target1), temp_set1 in upaths_set.iteritems():
            if (source1, target1) == (source, target):
                continue
            elif not temp_set.isdisjoint(temp_set1):
                has_common = True
        upaths_has_common[(source, target)] = has_common

    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # 如果和其他的都不相交
        if not upaths_has_common[(source, target)]:
            e = "%s+%s <= 1;..." % (node2x[source], node2x[target])
            unpath_constraints.append(e)
        else:
            # length: [paths]
            length_dict = {}
            # 把路径按照长度来归类.同一个长度的不平衡路径全部乘起来，称之为Ki
            for upath in paths_between:
                length = len(upath)
                string = tuple([node2x[node] for node in upath])
                if length not in length_dict:
                    length_dict[length] = [string]
                else:
                    length_dict[length].append(string)
            #[paths][paths][paths]
            length_list = length_dict.values()
            products = []
            # print "%% (%s, %s)" % (source, target)
            for i in range(0, len(length_list) - 1):
                for j in range(i + 1, len(length_list)):
                    for path_in_group_i in length_list[i]:
                        for path_in_group_j in length_list[j]:
                            products.append(
                                set(path_in_group_i).union(set(path_in_group_j)))
            for product in products:
                unpath_constraints.append("+".join(product) +
                                          "<= %d;..." % (len(product) - 1))
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

def upaths_contraints_stupid(unpaths, node2x):
    u'''原始的最2B的求约束的方法的
    '''
    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # length: [paths]
        length_dict = {}
        # 把路径按照长度来归类.同一个长度的不平衡路径全部乘起来，称之为Ki
        for upath in paths_between:
            length = len(upath)
            string = tuple([node2x[node] for node in upath])
            if length not in length_dict:
                length_dict[length] = [string]
            else:
                length_dict[length].append(string)
        #[paths][paths][paths]
        length_list = length_dict.values()
        products = []
        # print "%% (%s, %s)" % (source, target)
        for i in range(0, len(length_list) - 1):
            for j in range(i + 1, len(length_list)):
                for path_in_group_i in length_list[i]:
                    for path_in_group_j in length_list[j]:
                        products.append(
                            set(path_in_group_i).union(set(path_in_group_j)))
        for product in products:
            unpath_constraints.append("+".join(product) +
                                        "<= %d;..." % (len(product) - 1))
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

class ESScanApp(ScanApp):

    def __init__(self, name="ESScan"):
        super(ESScanApp, self).__init__(name)

    def _get_scan_fds(self, vm):
        graph = get_graph(vm)
        esgrh = ESGraph(graph)
        esgrh.save_info_item2csv(os.path.join(self.opath, "esgrh_records.csv"))
        self.fds = filter(cc.isDff, graph.nodes_iter())
        self.scan_fds = get_scan_fds(esgrh, self.opath)
        #esgrh.remove_nodes_from(self.scan_fds)
        #assert(isbalanced(esgrh))

if __name__ == "__main__":
    ESScanApp().run()
