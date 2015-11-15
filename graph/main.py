# -*-coding: utf-8 -*- 
import os

from netlistx.file_util import vm_files
from netlistx.exception import *

from netlistx.graph.circuitgraph import get_graph, save_graphs, fanout_stat
from netlistx.graph.cloudgraph import CloudRegGraph
import netlistx.graph.crgraph as old

class GraphFunc:
    def __init__(self):
        self.path = ""

    def crgraph(self):
        opath = os.path.join(self.path, "oldCrgraphs")
        if not os.path.exists(opath):
            os.mkdir( opath )
        for eachVm in vm_files(self.path):
            inputfile =os.path.join(self.path, eachVm)
            g2 = get_graph( inputfile )
            g2.info()
            cr2 = old.CloudRegGraph(g2, debug = True) 
            cr2.info()
            cr2.to_gexf_file( opath + "\\%s_crgraph.gexf" % cr2.name)
            cr2.snapshot(opath)

    def cloudgraph(self):
        for eachVm in vm_files(self.path):
            inputfile =os.path.join(self.path, eachVm)
            g2 = get_graph( inputfile )
            g2.info()
            #try:
            cr2 = CloudRegGraph(g2)
            cr2.info()
            cr2.snapshot(self.path + "\\CloudGraphs\\" +g2.name )
            cr3 = old.CloudRegGraph(g2, debug = True)
            cr3.info()
            cr3.snapshot(self.path + "\\oldCrgraphs\\" + g2.name )
            #except CrgraphError:
            #    print "Waring:", g2.name, "Cannot has a valid CloudGraph"
            #    continue

    def circuitgraph(self):
        print u"命令行帮助，可选命令如下"
        print u"grh:输入一个文件名称，分别生成两个图（包含和不包含PIPO），保存图的信息到\\test\\GexfDotGraphs下"
        print u"fanout:输入一个文件名称，统计其中组合逻辑和FD节点的扇出数目统计"
        print u"get:输入一个文件，获取并返回图.打印图的基本信息"
        cmd = raw_input("graph>:")
        if cmd == "grh" : 
            for eachfile in vm_files(self.path):
                inputfile = os.path.join( self.path, eachfile)
                save_graphs(inputfile, self.path + "\\GraphGexf")
        if cmd == "fanout":
            g1 = get_graph()
            fanout_stat(g1)
        if cmd == "get":
            fname = raw_input("plz enter filename:")
            g1 = get_graph(os.path.join(self.path, fname) )
            g1.info()
        else:
            return None

    def print_usage(self):
        print "-------------------usage----------------------------"
        print u"setpath: 设置vm文件存放的目录"
        print u"cloud:   对path下的vm文件进行CloudRegGraph建模"
        print u"help:    产生这个提示"
        print u"oldcr:   使用crgraph模块对电路进行CloudRegGraph建模"
        print u"graph:   进入graph子程序"
        print "----------------------------------------------------"

class GraphMainApp(GraphFunc):

    def __init__(self):
        GraphFunc.__init__(self)
        self.path = "\\test"
        self.cmd = ""
        self.opt = ""
        self.call = {}
        self.__bindcmd2func()

    def __bindcmd2func(self):
        '''将cmd命令和调用的函数绑定
        '''
        self.call["help"]  = self.print_usage
        self.call["cloud"] = self.cloudgraph
        self.call["graph"] = self.circuitgraph
        self.call['oldcr'] = self.crgraph 
        self.call["setpath"] = self.set_path
 
    def getcmd( self):
        args = raw_input("netlistx>:").split()
        self.cmd = args[0]
        self.opt = args[1:]

    def set_path( self):
        self.path = raw_input("plz enter path>") if not self.opt else self.opt
        if not os.path.exists( self.path):
            print "Invalid path"
            self.set_path()

    def run(self):
        self.set_path()
        while(1):
            self.getcmd()
            try:
                callfunc = self.call[self.cmd]
            except KeyError:
                if self.cmd == "exit":
                    break
                else:
                    print "Cannot recognize cmd:", self.cmd
                    self.call['help']()
            else:
                callfunc()
if __name__ == "__main__":  
    App = GraphMainApp()
    App.run()

