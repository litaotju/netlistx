# -*-coding: utf-8 -*- 
import os
import sys
import logging

import networkx as nx

import netlistx.graph.crgraph as old
from netlistx.cliapp import CliApp
from netlistx.log import logger
from netlistx.file_util import vm_files2
from netlistx.exception import *
from netlistx.graph.circuitgraph import get_graph, save_graphs, fanout_stat
from netlistx.graph.cloudgraph import CloudRegGraph
from netlistx.graph.esgraph import ESGraph

from netlistx.scan.util import get_namegraph, upath_cycle
from netlistx.scan.cycles import simple_cycles
from netlistx.prototype.unbpath import unbalance_paths

class GraphMainApp(CliApp):

    def __init__(self):
        CliApp.__init__(self, "GraphApp")
        self.addFunction("cloud", self.cloudgraph )
        self.addFunction("graph", self.circuitgraph)
        self.addFunction('oldcr', self.crgraph )
        self.addFunction("esgrh", self.esgraph )
        self.__setOpath = self.setOpath

    def runProcess(self, process):
        u'''@breif:根据模式，对一个目录或者一个单独的文件运行一个 process, process
            @param:
                process, a function( single file) with to handle a file
            @return:=
                void
        '''
        if self.mode == GraphMainApp.MODE_INTERACTIVE:
            if self.current_file != "":
                process( self.current_file )
            else:
                print "Warning: no current file opened. use command: readvm filename"
        else:
            map(process, vm_files2(self.path) )

    def crgraph(self):
        u'''为当前目录下的所有vm文件，生成旧的CloudRegGraph, 保存snapshot到 oldCloudGraphs
        '''
        self.__setOpath("oldCloudGraphs")
        def __process(eachVm):
            g = get_graph( eachVm )
            g.info()
            cr = old.CloudRegGraph(g, debug = True) 
            cr.info()
            cr.to_gexf_file( self.opath + "\\%s_CloudRegGraph.gexf" % cr.name)
            cr.snapshot( os.path.join( self.opath, g.name) )
            return
        self.runProcess( __process )

    def cloudgraph(self):
        u'''为当前目录下的所有vm文件 生成CloudRegGraph, 保存snapshot到CloudGraphs
        '''
        self.__setOpath("CloudGraphs")
        def __process(eachVm):
            g = get_graph( eachVm )
            g.info()
            cr = CloudRegGraph(g)
            cr.info()
            cr.snapshot( os.path.join( self.opath, g.name ) )
            return
        self.runProcess( __process )

    def circuitgraph(self):
        u'''和直接生成 图 相关的子程序
        '''
        self.__setOpath("Graphs")
        def __process(eachVm):
            graph= get_graph( eachVm )
            graph.info()
            if self.opt and self.opt[0] =='-fanout':
                fanout_stat(graph)
            return
        if self.mode == GraphMainApp.MODE_BATCH:
            map(save_graphs, vm_files2(self.path), [self.opath]*len( list(vm_files2(self.path )) ) )
        else:
            self.runProcess( __process )
        return

    def esgraph( self):
        u'''提取当前路径下的所有vm文件的 ESGraph
        '''
        self.__setOpath("ESGraph")
        csvfile = os.path.join( self.opath, "records.csv" )
        def __process(eachVm):
            g = get_graph( eachVm )
            es = ESGraph( g )
            selfloop_nodes = [node for node in es.nodes_iter()
                    if es.has_edge(node, node)]
            es.save_info_item2csv( csvfile )
            logger.info( es.info() )
            es.remove_nodes_from(selfloop_nodes)
           
            name_graph = get_namegraph(es)


            #从大到小排列触发器的出度
            nodes = name_graph.nodes()
            nodes.sort(key=name_graph.out_degree, reverse=True)
            p = os.path.join(self.opath, es.name)
            if not os.path.exists(p):
                os.makedirs(p)
            fobj = open(p+".degrees.csv", 'w')
            fobj.write("nodes, out_dgree\n")
            for eachNode in nodes:
                fobj.write("%s, %d\n" %(eachNode, name_graph.out_degree(eachNode)))
            fobj.close()

            #移除出度最大的
            #i = 2
            #remove_nodes = nodes[int(len(nodes)*0.2)*i : int(len(nodes)*0.2)*(i+1)]
            #name_graph.remove_nodes_from(remove_nodes)
            #打印环和不平衡路径的信息 
            #cycles_cnt = 0
            #for c in simple_cycles(name_graph):
            #    cycles_cnt += 1
            #    print "cycles cnt: %d" % cycles_cnt
            #u = unbalance_paths(name_graph)
            #logger.info("UNPS: %d " % len(u))
            #logger.info("Cycles: %d" % len(c))
            return
        self.runProcess(__process)
        return 

if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    app = GraphMainApp()
    app.run()

    
