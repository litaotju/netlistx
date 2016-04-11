# -*-coding: utf-8 -*- 
import os
import sys
import logging

import networkx as nx

import netlistx.graph.crgraph as old
from netlistx.log import logger
from netlistx.file_util import vm_files2, StdOutRedirect
from netlistx.exception import *
from netlistx.graph.circuitgraph import get_graph, save_graphs, fanout_stat
from netlistx.graph.cloudgraph import CloudRegGraph
from netlistx.graph.esgraph import ESGraph


class GraphFunc:
    '''一个抽象类，一些命令和函数的绑定，给出命令就运行相应的函数
    '''
    def __init__(self):
        self.path = ""
        self.opath = "" #设置输出路径
        self.call = {}
        self.__bindcmd2func()

    def __bindcmd2func(self):
        u'''将cmd命令和调用的函数绑定
        '''
        self.call["help"]  = self.print_usage
        self.call["cloud"] = self.cloudgraph
        self.call["graph"] = self.circuitgraph
        self.call['oldcr'] = self.crgraph 
        self.call["esgrh"] = self.esgraph

    def __setOpath( self, outpath ):
        u'''设置当前的输出路径
        '''
        if not os.path.isabs( outpath):
            self.opath = os.path.join( self.path, outpath )
        else:
            self.opath = outpath
        if not os.path.exists( self.opath ):
            os.mkdir( self.opath )
        return self.opath

    def crgraph(self):
        u'''为当前目录下的所有vm文件，生成旧的CloudRegGraph, 保存snapshot到 oldCloudGraphs
        '''
        self.__setOpath("oldCloudGraphs")
        for eachVm in vm_files2(self.path):
            g = get_graph( eachVm )
            g.info()
            cr = old.CloudRegGraph(g, debug = True) 
            cr.info()
            cr.to_gexf_file( self.opath + "\\%s_CloudRegGraph.gexf" % cr.name)
            cr.snapshot( os.path.join( self.opath, g.name) )

    def cloudgraph(self):
        u'''为当前目录下的所有vm文件 生成CloudRegGraph, 保存snapshot到CloudGraphs
        '''
        self.__setOpath("CloudGraphs")
        for eachVm in vm_files2(self.path):
            g = get_graph( eachVm )
            g.info()
            cr = CloudRegGraph(g)
            cr.info()
            cr.snapshot( os.path.join( self.opath, g.name ) )

    def circuitgraph(self):
        u'''和直接生成 图 相关的子程序
        '''
        usage = os.linesep.join([ u"命令行帮助，可选命令如下",
                                u"batch:   对当前路径下的vm文件分别生成两个图（包含和不包含PIPO），保存图的信息到 self.opath下",
                                u"single:  输入一个文件名称，统计其中组合逻辑和FD节点的扇出数目统计",
                                u"fanout:     输入一个文件，获取并返回图. 打印图的基本信息"])
        self.__setOpath("Graphs")
        graph = None
        while True:
            cmd = raw_input("graph>:")
            if cmd == "batch" : 
                for eachfile in vm_files2(self.path):
                    save_graphs( eachfile, self.opath )
            elif cmd == "single":
                fname = os.path.join(self.path, raw_input("enter a filename:") )
                graph= get_graph( fname )
                graph.info()
            elif cmd == "fanout":
                if graph is not None:
                    fanout_stat(graph)
                else:
                    print "Has no graph in, type: single command to produce one"
            elif cmd in ["quit", "exit", 'q']:
                break
            else:
                print usage
        return

    def esgraph( self):
        u'''提取当前路径下的所有vm文件的 ESGraph
        '''
        self.__setOpath("ESGraph")
        for eachVm in vm_files2(self.path):
            g = get_graph( eachVm )
            logger.debug("Get graph OKAY")
            es = ESGraph( g )
            logger.debug("Get ES OKAY")
            logger.info( es.info() )

    def print_usage(self):
        u'''打印用法信息
        '''
        print "--------------------------usage----------------------------"
        print os.linesep.join( [ "%10.10s : %s" % (cmd, func.__doc__) 
                                  for cmd, func in self.call.iteritems() ] )
    def add_function(self, cmd, func):
        u'''@brief:为app添加新的 cmd-func对，添加新的功能
            @params:
                cmd, a string indicate the cmd from user
                func, a callable object for cmd
        '''
        assert callable(func), "%s is not call able" % func
        if self.call.has_key(cmd):
            override = raw_input( "Waring: all ready have a cmd%s, do you want to override: (yes?no)" % cmd)
            if override == 'yes':
                self.call[cmd] = func
        else:
            self.call[cmd] = func

    def run():
        raise NotImplementedError


class GraphMainApp(GraphFunc):

    def __init__(self):
        GraphFunc.__init__(self)
        self.DEFAULT_PATH = os.getcwd()
        self.name = "netlistx"

        self.path = self.DEFAULT_PATH #默认路径为 os.getcwd()当前路径
        self.cmd  = ""
        self.opt  = None
        
        self.add_function('cd', self.setPath   )
        self.add_function('pwd', self.printPath)
        self.add_function("ls", self.listPath  )
        if os.name == 'nt':
            self.add_function('clear', lambda: os.system("cls") )
    
    def getCmd( self ):
        u'''打印netlistx:>prompt提示，并获取命令和选项
        '''
        leaf_path = os.path.split( self.path )[-1] #当前路径的最后一级
        prompt =  "[%s@%s]>:"% (self.name, leaf_path)
        args = raw_input(prompt).split()
        self.cmd = args[0]
        self.opt = args[1:]

    def setPath(self):
        u'''设置工作路径, 如果指定目录不存在，当前目录保持不变，并打印当前绝对目录
         '''
        path = raw_input("plz enter path>") if not self.opt else self.opt[0]
        #保持path的绝对路径属性
        if not os.path.isabs(path):
            path = os.path.join( self.path, path)
        #存在则更新，不存在打印当前路径
        if os.path.exists( path ):
            self.path = path
        else:
            print "Warning: invalid path."
            self.printPath()
        return
        
    def printPath(self):
        u'''显示当前绝对路径
        '''
        print "Current abs path is: ", self.path

    def listPath(self):
        u'''列出当前工作目录下的信息
        '''
        print "    ".join( os.listdir(self.path) )

    def run(self):
        while True:
            self.getCmd()
            callfunc = self.call['help'] #默认调取help函数
            try:
                callfunc = self.call[self.cmd]
            except KeyError:
                if self.cmd in [ "exit", "quit", "q"]:
                    break
                else:
                    print "Error: cannot recognize cmd:", self.cmd
            callfunc()
    
if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    app = GraphMainApp()
    app.run()

    
