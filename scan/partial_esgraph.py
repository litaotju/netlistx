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
    nx.write_dot(namegraph, os.path.join(opath, 'with-selfloop',esgrh.name + ".dot"))
    
    namegraph.remove_nodes_from(selfloop_nodes)

    nx.write_dot(namegraph, os.path.join(opath, 'without-selfloop', esgrh.name + ".dot"))
    
    unpaths, cycles = upath_cycle(namegraph)  #unpaths = [], cycles = []

    upath_json = open(os.path.join(opath, esgrh.name + "_upath.json"), 'w')
    cycle_json = open(os.path.join(opath, esgrh.name + "_cycle.json"), 'w')
    json.dump({("%s->%s" % (key[0], key[1])): value for key,value in unpaths.iteritems()}, 
              upath_json, 
              indent=4,
              separators=(",",":"))
    json.dump(cycles, cycle_json, indent=4)
    upath_json.close()
    cycle_json.close()

    ##FOR_DEBUG
    ##计算 理论上约束的个数
    number_of_constraints = 0
    fobj = open(os.path.join(opath, esgrh.name + "_upath.txt"), 'w')
    for (s, t), paths in unpaths.iteritems():
        number_of_cons_this = 0   #本对 (s,t) 所需要的约束条件数目
        number_of_eachLength = {} #本对 (s,t) 每一个长度的path的 数目
        for p in paths:
            if len(p) not in number_of_eachLength:
                number_of_eachLength[len(p)] = 1
            else:
                number_of_eachLength[len(p)] += 1
        fobj.write("%s->%s, upaths:%d, groups:[" % (s, t, len(paths)))
        fobj.write(" ,".join([str(value) for value in number_of_eachLength.values()]))
        fobj.write("]")

        # list of tuple(length, number_of_path_in_this_length_group)
        number_of_eachLength = list(number_of_eachLength.iteritems()) 
        groups = len(number_of_eachLength)
        for i in range(groups-1):
            for j in range(i+1, groups):
                number_of_cons_this += number_of_eachLength[i][1] * number_of_eachLength[j][1]
        fobj.write(", constraints :%d\n" % number_of_cons_this)
        number_of_constraints += number_of_cons_this

    ##FOR_DEBUG
    esgrh.save_info_item2csv(os.path.join(opath, "esgrh_records.csv"))
    fobj.write("ESGraph:%s has %d UNPs, %d cycles, %d self-loops" % \
                    (esgrh.name, len(unpaths), len(cycles), len(selfloop_nodes)))
    fobj.write("ESGraph:%s has %d unpath constraints" % (esgrh.name, number_of_constraints))
    fobj.close()

    # {name: x%d}
    node2x = {node: "x(%d)"%index for index, node in enumerate(namegraph.nodes())}
    constraints = gen_constraints(cycles, unpaths, node2x)

    scan_fds = []
    if constraints:
        gen_m_script(constraints, node2x, solution_file, port, script_file)
        #run_matlab(script_file, port)
        #scan_fds = read_solution(os.path.join(opath, solution_file), node2x) + selfloop_nodes
        scan_fds = []
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

    ##TODO:完善不平衡路径约束
    unpath_constraints = []
    ##获取不平衡路径的约束
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
        #print "%% (%s, %s)" % (source, target)
        for i in range(0, len(length_list)-1):
            for j in range(i+1, len(length_list)):
                for path_in_group_i in length_list[i]:
                    for path_in_group_j in length_list[j]:
                        products.append(set(path_in_group_i).union(set(path_in_group_j)))
        for product in products:
            unpath_constraints.append("+".join(product) +\
                                      "<= %d;..." % (len(product)-1))
    logger.critical("ESGraph generated %d matlab upath constraints" % len(unpath_constraints))
    return cycle_constaints + unpath_constraints

def main():
    "main function"
    PATH = raw_input("plz enter vm files path:")
    if not os.path.exists(PATH):
        print "Error: %s doesn't exists" % PATH
        sys.exit(-1)
    OPATH = os.path.join(PATH, "ESMatlab")
    if not os.path.exists(OPATH):
        os.mkdir(OPATH)
    for eachVm in vm_files2(PATH):
        graph = get_graph(eachVm)
        esgrh = ESGraph(graph)
        get_scan_fds(esgrh, OPATH)

if __name__ == "__main__":
    main()
