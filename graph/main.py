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
            @return:
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
            es.save_info_item2csv( csvfile )
            logger.info( es.info() )
            return
        self.runProcess(__process)
        return 

if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    app = GraphMainApp()
    app.run()

    
