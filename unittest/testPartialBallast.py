import unittest

import networkx as nx

from netlistx.scan.partialBallast import *

class Test_testPartialBallast(unittest.TestCase):

    def test_IntgraphFAS(self):
        g1 = nx.DiGraph()
        g1.add_path([0,1,2,0])
        g1.add_path([2,3,4,2])
        fas = feedbackset( g1 )
        print "FAS", fas
        self.assertEqual ( len(fas), 2)


    def test_IntgraphBalance(self):
        g2 = nx.DiGraph()
        g2.add_path([1,0,5,1])
        g2.add_path([5,1,3,5])
        g2.add_path([2,1,3,2])
        g2.add_path([5,4,3,5])

        fas2 = feedbackset( g2 )
        r  = balance(g2 )
        self.printresult( fas2, r)

    def test_IntgraphSelfloop(self):
        g = nx.DiGraph()
        g.add_edge(0,0)
        fas = feedbackset( g )
        r = balance( g )
        self.printresult( fas, r)
    
    def testParaType(self):
        g = nx.Graph()
        fas = feedbackset( g )
        self.assertRaises(Exception, balance( g ))

    def printresult(self, fas, r):
        print "FAS is %s" % fas
        print "R is : %s" % r

if __name__ == '__main__':
    unittest.main()
