#! -*- coding:utf-8 -*-

import os
import logging
import networkx as nx
import matplotlib.pylab as plt

import itrans
import Primitives



def combNodes(g ):
    selenments_types = [Primitives.dffkeyword, 'input', 'output']
    node_type = node_type = nx.get_node_attributes(g, 'label')
    result =  [node for node in g.nodes_iter() if node_type[node] not in selenments_types]
    return result

def getSgraph(g):
    assert( isinstance(g, nx.DiGraph))
    for node in combNodes(g):
        for prenode in g.predecessors_iter( node ):
            for succnode in g.successors_iter( node ):
                g.add_edge( prenode, succnode )
        g.remove_node(node)
    return g

def test_A():

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

    nx.write_dot(g, "bench.dot" )
    print nx.info(g)
    #plt.figure("Before")
    #nx.draw_networkx(g)
    #plt.show()

    getSgraph(g)
    nx.write_dot(g, "benchSgraph.dot" )
    print nx.info(g)
    #plt.figure("After")
    #nx.draw_networkx(g)
    #plt.show()

def sgraphyDir( path ):
    if not os.path.exists(path):
        raise Exception("%s does not exist", path )
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)) and filename.split(".")[1] == "v":
            base = filename.split(".")[0]
            filename = os.path.join( path, filename)

            dffs, coms = itrans.classify( itrans.trans(filename) )
            graph = itrans.graphy(dffs, coms, base)

            logging.info( base )
            logging.info( "number of self-loop node: %d" % graph.number_of_selfloops())
            logging.info( nx.info(graph) )
            
            nx.write_dot( graph, os.path.join(path, base + ".dot" ))
            nx.write_dot( getSgraph(graph), os.path.join(path, base + "_s.dot"))
            print "finished"

if __name__ == "__main__":
    path = raw_input("plz enter path:")
    logging.basicConfig(level=logging.INFO,
                #format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename= os.path.join(path, 'iscas89_sgraph.log'),
                filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logger = logging.getLogger('')
    logger.addHandler(console)
    sgraphyDir( path )

