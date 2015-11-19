import unittest

import networkx as nx
from netlistx.prototype.fas import comb_fas

class Test_testFas(unittest.TestCase):
    def test_Fig2inPaper(self):
        'graph from paper [2001 combinatorial fas] Figure2'
        graph = nx.DiGraph()
        graph.add_edge(1,5, weight = 5)
        graph.add_edge(2,1, weight = 4)
        graph.add_edge(5,2, weight = 6)
        graph.add_edge(4,5, weight = 7)
        graph.add_edge(2,4, weight = 5)
        graph.add_edge(4,3, weight = 2)
        graph.add_edge(3,2, weight = 6)        
        fas = comb_fas( graph)
        expected = [(5,2), (4,3)]
        self.assertEqual( fas, expected)
    
    def test_UserDefinedGraph(self):
        graph = nx.DiGraph()
        weighted_edges = [ ('A','B',20 ),('B','A', 10), ('B','C', 20),('C','A', 5) ]
        graph.add_weighted_edges_from( weighted_edges)
        fas = comb_fas( graph)
        expected = [('C','A'),('B','A')]
        self.assertListEqual( fas, expected )

if __name__ == '__main__':
    unittest.main()
