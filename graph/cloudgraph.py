# -*- coding: utf-8 -*-

#built-in
import os
import time

#3-rd party
import networkx as nx

#user-defined
import netlistx.class_circuit as cc
import netlistx.graph.crgraph as old

from netlistx.exception import CrgraphError
from netlistx.file_util import vm_files
from netlistx.graph.circuitgraph import CircuitGraph
from netlistx.graph.circuitgraph import get_graph

__all__ = ["CloudRegGraph" ]
class CloudRegGraph(nx.DiGraph):
    """node as cloud, edge as fds"""
    REMAIN_FD_PORT = ['D','Q']

    def __init__(self, graph):
        '''@param: graph, a CircuitGraph obj
                   every node is a cc.port obj or cc.circuit_module obj
        '''
        print "Job: getting CloudRegGraph.."
        assert isinstance( graph, CircuitGraph), str(graph.__class__)
        assert graph.include_pipo == True

        nx.DiGraph.__init__(self)
        self.name = graph.name+ "_cloudgraph"
        self.clouds = []
        self.fds = []
        self.constfds = []
        self.arcs = {}

        self.__getself(graph)
        self.__merge()
        self.__fd2edge()
        print "Job: CloudRegGraph grt.OK!"

    def __getself(self, graph):
        gcopy = graph.topo_copy()
        fds = [ node for node in gcopy.nodes()if isfd( node ) ]
        vccgnd = [node for node in gcopy.nodes() if isvccgnd( node ) ]
        gcopy.remove_nodes_from( fds + vccgnd)
        
        # nodes
        ccnt = 0
        clouds = []
        for cloud in nx.weakly_connected_component_subgraphs(gcopy, copy = False):
            ccnt += 1
            tmpgraph = nx.DiGraph( cloud, name = "cloud%d" % ccnt )
            clouds.append( tmpgraph )
        nodes = fds + clouds
        print "Info: %d connected_componenent subgraph after remove FD [GND_VCC]*" % len(clouds)
        # edges
        constfds = []
        edges = []
        for pre, succ, data in graph.edges_iter(data = True ):
            port_pairs = data['port_pairs']
            for port_pair in port_pairs:
                preport = port_pair[0].name
                succport = port_pair[1].name
                credge = ()

                #两个D触发器相连接
                if isfd( pre ) and isfd( succ):
                    if (preport not in  CloudRegGraph.REMAIN_FD_PORT)\
                        or (succport not in CloudRegGraph.REMAIN_FD_PORT):
                        continue
                    ccnt += 1
                    empty = nx.DiGraph(name = "empty_cloud%d" % ccnt )
                    edges.append( (pre, empty) )
                    edges.append( (empty, succ) )
                    continue
            
                # D触发器连接到非D触发器
                elif isfd( pre ):
                    #注意，常数的D触发器在这一步可能会加入进来
                    fdport = preport
                    credge = self.__credge( pre,  succ, clouds, fdport, fdispre = True)

                # 非D触发器连接到D触发器
                elif isfd( succ ):
                    if isvccgnd( pre ):
                        constfds.append( succ )
                        continue
                    fdport = succport
                    credge = self.__credge( succ, pre, clouds, fdport, fdispre = False)
                if credge: edges.append( credge )

        self.add_nodes_from( nodes)
        self.add_edges_from( edges)
        
        #移除不必要节点，包括constfd, solocloud
        self.remove_nodes_from( constfds )
        solocloud = [cloud for cloud in clouds if self.degree(cloud) == 0]
        self.remove_nodes_from( solocloud )

        self.fds = [node for node in self.nodes() if isfd(node) ]
        self.constfds = constfds
        self.clouds = clouds

        self.check()

    def __credge(self, fd, nonfd, clouds, fdport, fdispre):
        '''是为了找出FD与Non-FD相连接的边
        '''
        credge = ()
        if fdport not in CloudRegGraph.REMAIN_FD_PORT:
            return credge
        else:
            for cloud in clouds:
                if cloud.has_node( nonfd ):
                    credge = (fd, cloud ) if fdispre else (cloud, fd)
            if not credge:
                err = "None of the cloud has node:%s %s , " % ( nonfd.__class__, nonfd.name )
                err += "FD: %s, FD_PORT: %s" %( fd.name, fdport)
                raise CrgraphError, err
        return credge

    def __merge(self):
        for fd in self.fds:
            succs = self.successors( fd)
            if len(succs ) <= 1:
                continue
            else:
                # TODO: 制约系统速度的关键
                big_cloud = nx.union_all(succs)
                # ----
            pre_fds = set()
            succ_fds = set()
            for succ_cloud in succs:
                assert isinstance(succ_cloud, nx.DiGraph)
                pre_fds = pre_fds.union( set( self.predecessors(succ_cloud) ) )
                succ_fds = succ_fds.union( set( self.successors( succ_cloud) ) )
                self.remove_node(succ_cloud)
            self.add_node( big_cloud, label = big_cloud.name)
            self.add_edges_from( [ (pre_fd, big_cloud) for pre_fd in pre_fds] )
            self.add_edges_from( [ (big_cloud, succ_fd) for succ_fd in succ_fds] )
        for fd in self.fds:
            if self.out_degree(fd) > 1 or self.in_degree(fd) != 1:
                err = "Error: %s indegree:%d outdegree:%d" %\
                    (fd, self.in_degree(fd), self.out_degree(fd) )
                raise CrgraphError, err 
            elif self.out_degree(fd) < 1:
                self.remove_node( fd)
                print "Waring FD:%s has no succ. Removed" % fd.name 
        self.fds = [node for node in self.nodes_iter() if isfd(node )]
        self.check()

    def __fd2edge(self):
        arc = {}
        for fd in self.fds:
            precs = self.predecessors( fd )
            succs = self.successors( fd )
            prec = precs[0]
            succ = succs[0] 
            assert isinstance(prec, nx.DiGraph)
            assert isinstance(succ, nx.DiGraph)
            if not arc.has_key( (prec, succ) ):
                arc[ (prec, succ )] = []
            arc[(prec, succ)].append( fd )
            self.remove_node( fd )
        assert self.number_of_edges() == 0
        remain_reg = 0
        for edge, reg in arc.iteritems():
            fdnum = len( reg )
            remain_reg += fdnum
            self.add_edge(edge[0], edge[1], weight = fdnum, label = fdnum)
        self.check()
        self.arcs = arc

    def info(self , verbose = False):
        print "------------------------------------------------------"
        print "CloudRegGraph info:"
        print nx.info(self)
        ncloud = 0
        nreg = 0
        for node in self.nodes_iter():
            if isinstance(node, nx.DiGraph): 
                ncloud += 1
                if node.number_of_nodes() == 0:
                    if verbose: print "%s ::\n empty cloud\n" % node.name
                    continue
                elif verbose: print "%s::" % node.name
                for prim in node.nodes_iter():       
                    if verbose: print prim.name
            else:
                assert isfd(node)
                if verbose: print "FD:: %s %s \n" % (node.cellref, node.name)
                nreg += 1
        print "Number of cloud      : %d" % ncloud
        print "Number of remainfd   : %d" % len(self.fds)
        print "Number of constfd    : %d" % len( self.constfds)
        print "---------------------------------------------------"

    def snapshot(self, path):
        '''@param： path, 一个输出路径
           @brief: 将当前图中的所有cloud(nx.DiGraph)和fd(cc.circut_module)以
                    以dot的形式保存在当前路径中
        '''
        if not os.path.exists( path):
            os.makedirs( path)
        def nm( name ):
            return name[1:] if name[0] == "\\" else name
        #总的图
        namegraph = nx.DiGraph( name = self.name)
        for pre, succ, data in self.edges_iter(data = True):
            namegraph.add_edge( nm(pre.name), nm(succ.name),\
                 weight = data['weight'], label = data['label'])
        nx.write_dot( namegraph, os.path.join(path, self.name+".dot") )
        
        #各cloud
        for cloud in self.nodes_iter():
            if cloud.number_of_nodes() == 0:
                continue
            namegraph = nx.DiGraph(name = cloud.name)
            namegraph.add_nodes_from( [ nm(node.name) for node in cloud.nodes_iter() ] )
            namegraph.add_edges_from ( [ ( nm(edge[0].name), nm( edge[1].name ) ) for edge in cloud.edges_iter() ])
            nx.write_dot( namegraph, os.path.join(path , cloud.name + ".dot"))
        #fd边的记录
        out = open( os.path.join(path, self.name + "_arcs.txt"), 'w')
        for edge, fds in self.arcs.iteritems():
            out.write("\nEdge: %s, %s\n" % (edge[0].name, edge[1].name) )
            out.write("has %d FDs:\n" % len(fds) )
            for fd in fds:
                out.write("   %s %s \n" % (fd.cellref, fd.name) )
        out.close()
        print "Snapshot %s OK!" % self.name

    def check(self):
        for node in self.nodes_iter():
            if not isfd( node):
                assert isinstance(node, nx.DiGraph), str( node.__class__ )

def isfd( node):
    if isinstance(node, cc.circut_module) and node.m_type == 'FD':
        return True
    return False

def isvccgnd(node):
    if isinstance(node ,cc.circut_module ) and node.cellref in ['GND', "VCC"]:
        return True
    return False
