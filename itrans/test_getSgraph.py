import unittest

import networkx as  nx
import matplotlib.pyplot as plt

import sgraph
import Primitives

class Test_getSgraph(unittest.TestCase):
    def __init__(self, methodName = 'runTest'):
        self.bench = nx.DiGraph()
        self.bench_s = nx.DiGraph()
        self.initBench()
        self.initBenchSgraph()
        return super(Test_getSgraph, self).__init__(methodName)

    def initBench(self):
        g = nx.DiGraph()
        g.add_nodes_from("ABCD", label = 'input')
        g.add_nodes_from("XY", label = 'output')
        g.add_nodes_from(["FF1", "FF2", "FF3", "FF4"], label = Primitives.dffkeyword)
        g.add_nodes_from(range(1,8), label = "comb")

        g.add_edge("A",1)
        g.add_edges_from([("B",1), ("B",3)])
        g.add_edge("C",3)
        g.add_edge("D",2)
    
        g.add_edge("FF1",4)
        g.add_edges_from([ ("FF2", 5), ("FF2", 6) ])
        g.add_edge("FF3", 7)
        g.add_edge("FF4", "Y")

        g.add_edge(1, "FF2")
        g.add_edge(2, "FF1")
        g.add_edge(3, 4)
        g.add_edge(4, 6)
        g.add_edge(5, "FF3")
        g.add_edges_from( [ (6, 7), (6, "FF4")])
        g.add_edge(7, "X")
        self.bench = g
    
    def initBenchSgraph(self):
        g = nx.DiGraph()
        g.add_node

    def test_A(self):
        g = nx.DiGraph(self.bench)
        sgraph.getSgraph(g)


if __name__ == '__main__':
    unittest.main()
