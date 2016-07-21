import unittest
import os

import netlistx.circuit as cc
from netlistx.graph.circuitgraph import get_graph, fusionable_pair

class Test_testFusionablePair(unittest.TestCase):

    def setUp(self):
        super(Test_testFusionablePair, self).setUp()
        vmfile = os.path.join(os.path.dirname(__file__), "testGraph\\testLogicPair.vm")
        self.graph = get_graph(vmfile)

    def test_GetFusionablePair(self):
        K = 6
        pairs = fusionable_pair(self.graph, K)
        assert len(pairs)!=0
        for fd, lut in pairs:
            assert cc.isDff(fd)
            assert cc.isLUT(lut) and lut.input_count() <= K-2

if __name__ == '__main__':
    unittest.main()
