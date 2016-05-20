import unittest

import networkx as nx
from netlistx.prototype.unbpath import *

class Test_unbalance_paths(unittest.TestCase):
    def test_A(self):
        G = nx.DiGraph()
        edges = [('a','b'),('a','e'),('a','d'),('d','c'),('b','c'),('e','b')]
        G.add_edges_from(edges)
        upaths = unbalance_paths(G)
        self.assertDictEqual(upaths,
                             {('a','b'):[['a','b'],
                                         ['a','e','b']],
                              ('a','c'):[['a','b','c'],
                                         ['a','e','b','c'],
                                         ['a','d','c']]
                              })
        return

    def test_B(self):
        G = nx.DiGraph()
        edges = [('a','b'),('a','e'),('a','c'),('b','c'),('e','b')]
        G.add_edges_from(edges)
        upaths = unbalance_paths(G)
        self.assertDictEqual(upaths,
                                {('a','b'):[
                                        ['a','b'],
                                        ['a','e','b']],
                                 ('a','c'):[
                                        ['a','c'],
                                        ['a','b','c'],
                                        ['a','e','b','c']]
                                })
        return
    
class Test_find_upath(unittest.TestCase):
    def test_A(self):
        G = nx.DiGraph()
        edges = [('a','b'),('a','e'),('a','d'),('d','c'),('b','c'),('e','b')]
        G.add_edges_from(edges)
        cov = find_upath(G,'a')
        self.assertTrue('b' in cov)
        self.assertTrue('c' in cov)
        self.assertTrue(len(cov)==2)

    def test_B(self):
        G = nx.DiGraph()
        edges = [('a','b'),('a','e'),('a','c'),('b','c'),('e','b')]
        G.add_edges_from(edges)
        cov = find_upath(G,'a')
        self.assertTrue('b' in cov)
        self.assertTrue('c' in cov)
        self.assertTrue(len(cov)==2)

if __name__ == '__main__':
    unittest.main()
