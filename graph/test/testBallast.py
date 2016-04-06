import unittest

import networkx as nx

from netlistx.exception import *
from netlistx.graph.ballast import Ballaster
from netlistx.graph.crgraph import CloudRegGraph
from netlistx.graph.circuitgraph import get_graph

class Test_testBallast(unittest.TestCase):

    def test_FAS(self):
        g1 = nx.DiGraph()
        g1.add_path([0,1,2,0])
        g1.add_path([2,3,4,2])
        b1 = Ballaster(g1)
        b1.feedbackset()
        print "FAS is %s" % g1.fas

    def test_Balance(self):
        g2 = nx.DiGraph()
        g2.add_path([1,0,5,1])
        g2.add_path([5,1,3,5])
        g2.add_path([2,1,3,2])
        g2.add_path([5,4,3,5])

        b2 = Ballaster(g2)
        b2.feedbackset()
        b2.balance(b2.intgraph)
        print "FAS is %s" % g2.fas

if __name__ == '__main__':
    unittest.main()
