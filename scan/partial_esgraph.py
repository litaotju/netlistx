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

#是否保存中间信息
INTERMEDIATE = True

#UNP约束生成方法选择
SIMPLE = 1  
COMPLEX = 2
STUPID = 3
MERGE_GROUP = 4
#生成UNP约束的级别，可在1,2,3,4中选一个
LEVEL = MERGE_GROUP

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
    #if constraints:
    #    gen_m_script("-sum(x)", constraints, len(node2x),
    #                 solution_file, port, script_file)
    #    run_matlab(script_file, port)
    #    scan_fds += read_solution(os.path.join(opath, solution_file), node2x)
    scan_fds = [namegraph.original_node[name] for name in scan_fds]
    
    esgrh.remove_nodes_from(scan_fds)

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
    elif LEVEL == SIMPLE:
        unpath_constraints = upaths_contraints_simple(unpaths, node2x)
    else:
        unpath_constraints = upaths_contraints_more_complex(unpaths, node2x)
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


def upaths_contraints_complex(unpaths, node2x):
    u'''UNP相交的情况，考虑全部约束，否则只考虑起点和终点
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
                break
        upaths_has_common[(source, target)] = has_common

    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # 如果和其他的都不相交
        if not upaths_has_common[(source, target)]:
            e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
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
    u'''原始的最2B的求约束的方法，长度分组，然后相加
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


def upaths_contraints_more_complex(unpaths, node2x):
    u'''brief:
            对每一个UNP，判断其中每一个长度分组内的不平衡路径的是否和其他UNP有交集
                如果有，在约束中，将这一组的全部写出来
                如果没有，在约束中，将一组只认为是一条边
            同时，更新node2x的对应关系
        @params:
            unpaths, a dict of {(source:target):[[path1][path2]...]}
            node2x, a dict of { node:x(%d)}
        @return:
            upaths_contraints, a list of equation in string form, ["x1+x2<=1;...", "x2+x3<=1;..."...]
        @modify:
            modify the node2x
    '''
    upaths_set = {}
    
    #对每一个UNP的不平衡路径按照长度分组
    upaths_length_group_set = {}
    for (source, target), paths_between in unpaths.iteritems():
        temp_set = reduce(lambda x, y: x.union(set(y)), paths_between, set())
        upaths_set[(source, target)] = temp_set
        # length: [paths]
        length_dict = {}
        for upath in paths_between:
            length = len(upath)
            string = tuple([node2x[node] for node in upath])
            if length not in length_dict:
                length_dict[length] = [string]
            else:
                length_dict[length].append(string)
        #[paths][paths][paths]
        length_list = length_dict.values()
        upaths_length_group_set[(source, target)] = length_list

    upaths_has_common = {}
    group_has_common = {}
    
    ##求每一组是否和其他UNP中的一组有交集
    get_set_from_list_list = lambda group: reduce(lambda x, y: x.union(set(y[1:-1])), group, set())
    for (source, target), groups in upaths_length_group_set.iteritems():
        has_common = False
        for (source1, target1), groups1 in upaths_length_group_set.iteritems():
            if (source1, target1) == (source, target):
                continue
            for group in groups:
                # 一组内的所有路径上的所有内点，全部化为一个集合
                tempset = get_set_from_list_list(group)
                for group1 in groups1:
                    tempset1 = get_set_from_list_list(group1)
                    if tempset.intersection(tempset1):
                        has_common = True
                        group_has_common[(source,target,len(group[0]))] = True
                        group_has_common[(source1,target1,len(group1[0]))] = True
        upaths_has_common[(source, target)] = has_common
        upaths_has_common[(source1, target1)] = has_common

    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # 如果和其他的都不相交
        if not upaths_has_common[(source, target)]:
            e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
            unpath_constraints.append(e)
        else:
            #[paths][paths][paths]
            length_list = upaths_length_group_set[(source, target)]
            new_length_list = []
            products = []
            for group in length_list:
                #如果这一组没有和其他的有交集
                if not group_has_common.has_key((source,target,len(group[0]))):
                    #只取一条路径
                    new_length_list.append(merge_group(group,node2x))
                else: #如果和其他的组有交集，则取这一组全部的路径
                    new_length_list.append(group)
            length_list = new_length_list
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

def merge_group(group, node2x):
    u'''@breif:
            把一组同样长度（group内的路径）的不平衡路径替换成，一条路径，上面的每一个点的权重为组内路径的个数
        @params:
            group, a list of list, each of the list has same length
            node2x, dict {node->x }
        @return:
            [group[0]]
        @modifiy:
            node2x
    '''
    # len group >= 2
    # group中的每一个列表长度相等
    #对第一条之外的其他路径操作
    for i in range(1, len(group)):
        #内点, 将多个节点，映射为一个x
        for index, node in enumerate(group[i]):
            assert index < len(group[0])
            if index == 0 or index == len(group[i])-1:
                continue
            node2x[node] = node2x[group[0][index]]
    return [group[0]]

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
