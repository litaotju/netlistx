# -*-coding:utf-8 -*- #

import unittest
import os

import matplotlib.pylab as plt
from netlistx.graph.circuitgraph import get_graph
from netlistx.file_util import vm_files
from netlistx import CloudRegGraph

class Test_testCrgraph(unittest.TestCase):
    #------------------------------------------------------------------------------
    # 模块测试代码
    #------------------------------------------------------------------------------
    def setUp(self):
        '''crgraph本模块的测试
        '''
        self.path = os.path.dirname(__file__)+"\\crtest\\"
        print self.path
    def testCrgraphBase(self):
        path = self.path
        print path
        for eachVm in vm_files(path):
            g2 = get_graph(path+eachVm) # 输入netlist 文件，得到 CircuitGraph对象g2
            g2.info() #打印原图的详细信息
            cr2 = CloudRegGraph(g2) 
            cr2.info()
            cr2.to_gexf_file(path+"graph\\%s_crgraph.gexf" % cr2.name)
            if cr2.number_of_nodes() <= 100:
                cr2.paint(path+"graph\\")

if __name__ == '__main__':
    unittest.main()