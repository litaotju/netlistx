import unittest

import networkx as nx
from netlistx.scan.partialBallast import balance

class TestPartialBallast(unittest.TestCase):

    def testA(self):
        u'''在这个例子里balance是最优的
        '''
        a = nx.DiGraph()
        a.add_edge(1, 2, weight = 100)
        a.add_edge(1, 3, weight = 2)
        a.add_edge(1, 4, weight = 1)
        a.add_edge(3, 2, weight = 2)
        a.add_edge(4, 2, weight = 1)
        r = balance(a)
        self.assertListEqual([(1,3),(1,4)], r)

    def testB(self):
        u'''本例论证了ballast方法的非最优性
        '''
        a = nx.DiGraph()
        a.add_edge(1, 2, weight = 3)
        a.add_edge(1, 3, weight = 2)
        a.add_edge(1, 4, weight = 2)
        a.add_edge(3, 2, weight = 2)
        a.add_edge(4, 2, weight = 2)
        r = balance(a)
        self.assertListEqual([(1,3),(1,4)], r)

if __name__ == '__main__':
    unittest.main()
