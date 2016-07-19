# -*- coding: utf-8 -*-
u'''
本模块实现了一个使用增广S图的优化方法来进行部分扫描触发器的方法。
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
from netlistx.scan.util import (get_namegraph, upath_cycle, gen_m_script, 
                                        run_matlab, read_solution, isbalanced)
from netlistx.prototype.unbpath import unbalance_paths_deprecate
from netlistx.scan.scanapp import ScanApp

#如果是迭代的求解，那么使用BFS类似的方法寻找UNP
IS_ITER = False

#是否保存中间信息
INTERMEDIATE = False

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

    if IS_ITER:
        # 使用类似 BFS的方法来找UNP
        logger.debug("unpaths get okay")
        cycles = list(nx.simple_cycles(namegraph))
        logger.debug("cycles get okay")
    else:
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

    #如果生成的约束长度为0。直接返回，否则再进行Matlab求解
    if not constraints:
        scan_fds = [namegraph.original_node[name] for name in scan_fds]
        return scan_fds

    script_file = os.path.join(opath, esgrh.name + ".m")  # 输出的matlab脚本文件名，如果需要的话
    solution_file = esgrh.name + "_ESGraph_MatSolution.txt"  # matlab输出的解的文件名
    port = 12345  # Socket port for matlab

    # 生成目标函数
    obj = ""
    ## UNP之间的Paths没有合并的情况时
        weight = {}
        MAX_NODE = len(node2x) + 1000
        for entity, x in node2x.iteritems():
            # 触发器节点的权重设置为1
                weight[x] = 1
            else:
                #设置端口的权重极大，使得尽可能选择触发器
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
    
    # 产生Matlab脚本
    
    # 运行脚本，读取结果
    if LEVEL == 1:
        run_matlab(script_file, port)
        scan_fds += read_solution(os.path.join(opath, solution_file), node2x)
    
    #从字符串，获取真正的扫描触发器对象，
    scan_fds = [namegraph.original_node[name] for name in scan_fds]

    # 解里面可能有端口。保存解中的端口
    scan_ports = filter(cc.isPort, scan_fds)
    if scan_ports:
        with StdOutRedirect(os.path.join(opath, "ScanPorts_%s.txt" % esgrh.name)):
            for port in scan_ports:
                print(port.port_type + ":" + port.name)
    
    #将端口从图中移除
    esgrh.remove_nodes_from(scan_ports)
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
    # 获取不平衡路径的约束。 约束需要根据 LEVEL 调用不同的函数生成
    unpath_constraints = funcs_to_generate_unp_const[LEVEL](unpaths, node2x)
    return cycle_constaints + unpath_constraints


def upaths_contraints_simple(unpaths, node2x):
    u'''简单的生成UNP约束的方法：每一个UNP，只考虑起点和终点
    '''
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
        unpath_constraints.append(e)
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

#其他生成UNP约束的函数
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
    '''正常方法遍历方法得到UNP，然后生成Matlab求解问题
    '''
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

class ESScanAppCut(ScanApp):
    '''使用Cut图的方法，将大的图减小，然后分别求解
    '''
    def __init__(self, name="ESScanCut"):
        super(ESScanAppCut, self).__init__(name)

    def _get_scan_fds(self):
        raise NotImplementedError
        graph = CircuitGraph(self.netlist)
        esgrh = ESGraph(graph)
        esgrh.save_info_item2csv(os.path.join(self.opath, "esgrh_records.csv"))
        self.fds = filter(cc.isDff, graph.nodes_iter())

        ##找出 一个pi到一个po之间的最小的点割
        ports = filter(cc.isPort, graph.nodes_iter())
        pi = filter(lambda x: x.port_type == cc.Port.PORT_TYPE_INPUT, ports)[0]
        po = filter(lambda x: x.port_type == cc.Port.PORT_TYPE_OUTPUT, ports)[0]
        cut = nx.minimum_node_cut(esgrh, pi, po)
        self.scan_fds = filter(cc.isDff, cut)

        #移除点割，获得子图
        esgrh.remove_nodes_from(cut)

        #对每一个连通字图获取扫描触发器
        glist = nx.weakly_connected_component_subgraphs(esgrh, copy=False)
        for index, subgraph in enumerate(glist):
            subgraph.name = "{}_sub_{}".format(esgrh.name, index)
            scan_fds = get_scan_fds(subgraph, self.opath)
            esgrh.remove_nodes_from(scan_fds)

        assert(isbalanced(esgrh))
    
class ESScanAppIter(ScanApp):
    ''' 本APP适用于图比较复杂的情况，找UNP和找CYCLE都比较费时间。所以分两步求解
        1. 先移除图中部分的D触发器作为SFF。移除的比例由 PORTION_MOST_FANOUT_AS_SFF来决定
        2. 使用迭代的方法，逐次找UNP
    '''
    PORTION_MOST_FANOUT_AS_SFF = 0.2

    def __init__(self, name="ESScanIter"):
        global IS_ITER
        IS_ITER = True

    def _get_scan_fds(self):
        graph = CircuitGraph(self.netlist)
        esgrh = ESGraph(graph)
        esgrh.save_info_item2csv(os.path.join(self.opath, "esgrh_records.csv"))
        self.fds = filter(cc.isDff, graph.nodes_iter())
       
        #从大到小排列触发器的出度
        self.fds.sort(key=esgrh.out_degree, reverse=True)
        
        #取前 PORTION_MOST_FANOUT_AS_SFF 当作扫描触发器,先将这部分触发器从图中移除
        self.scan_fds = self.fds[ : int(len(self.fds)*self.PORTION_MOST_FANOUT_AS_SFF)]
        esgrh.remove_nodes_from(self.scan_fds)

        iter_cnt = 0
        #迭代求解，直到图变平衡
        while(not isbalanced(esgrh)):
            opath = os.path.join(self.opath, "iter%d" % iter_cnt)
            scan_fds = get_scan_fds(esgrh, opath)
            #每一轮的结果必然不为0，如果为0.说明图已经被平衡了
            iter_cnt += 1
            self.scan_fds += scan_fds
            esgrh.remove_nodes_from(scan_fds)
    
    def set_portion(self):
        u'设置 大扇出D触发器的转换为SFF的比例'
        portion = float(raw_input("plz set PORTION"))
            self.PORTION_MOST_FANOUT_AS_SFF = portion
        else:
            print "Ileagal Value, portion must >=0 and <=1"

def get_level():
    u'''从stdin获取level，默认为1
    '''
    level = int(raw_input("set level:"))
    if level < 1 or level > 5:
        level = 1
if __name__ == "__main__":
    app = ESScanApp()
    def get_level():
        level = int(raw_input("set level:"))
        if level < 1 or level > 5:
            level = 1
        LEVEL = level
    app = None
    try:
        app = app_ctxt[sys.argv[1]]()
    except KeyError: #参数不在 'normal' 'iter' 'cut'中时
        print "Usage: partial_esgraph [<normal> <iter> <cut>]"
        exit()
    except IndexError: #没有参数时
        app = ESScanAppIter()

    app.addFunction("level", get_level)
    app.run()
