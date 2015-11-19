# -*- coding:utf-8 -*- 

import copy
import networkx as nx

__all__ = [ 'comb_fas' ]

''' comb_fas is a implementation of the algorthm of 
    [2001 Combinatorial Algorithms for Feedback Problems in Directed Graphs].

'''

def get_edges(cycle):
    '''@param: cycle, a list of node [u1,u2,u3,..un] for cycle: u1->u2->u3->...un->u1
               or self loop [u1] for selfloop: u1->u1
    '''
    edges = []
    for i in range(0, len(cycle)-1):
        edges.append( (cycle[i], cycle[i+1]) )
    edges.append( (cycle[-1], cycle[0]) )
    return edges

def comb_fas( graph):
    '''@param: graph, a nx.DiGraph obj
    '''
    assert isinstance( graph, nx.DiGraph)
    weight = nx.get_edge_attributes( graph, 'weight')
    assert len(weight) == graph.number_of_edges(), "Some edge doesnot has a weight attr."
    fas = []
    while( not nx.is_directed_acyclic_graph(graph) ):
        c = list( nx.simple_cycles(graph) )[0]
        mini_weight = min( [ weight[edge] for edge in get_edges(c)] )

        cycle_edges_weight = {edge:weight[edge] for edge in get_edges(c) }
        for eachEdge in cycle_edges_weight.keys():
            cycle_edges_weight[eachEdge] -= mini_weight
            weight[eachEdge ] -= mini_weight
            if cycle_edges_weight[eachEdge] == 0:
                fas.append( eachEdge )
                graph.remove_edge( eachEdge[0], eachEdge[1] )

    for eachEdge in copy.copy(fas):
        graph.add_edge( eachEdge[0], eachEdge[1], {'weight' : weight[eachEdge]} )
        if nx.is_directed_acyclic_graph( graph):
            fas.remove(eachEdge)
            continue
        else:
            graph.remove_edge( eachEdge[0], eachEdge[1] )
    return fas

