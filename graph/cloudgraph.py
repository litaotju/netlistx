# -*- coding: utf-8 -*-

#built-in
import os

#3-rd party
import networkx as nx

#user-defined
import netlistx.class_circuit as cc
from netlistx.file_util import vm_files

from circuitgraph import CircuitGraph
from circuitgraph import get_graph
import crgraph as old

class CloudRegGraph(nx.DiGraph):
    """new CloudRegGraph class"""
    REMAIN_FD_PORT = ['D','Q']

    def __init__(self, graph):
        '''@param: graph, a CircuitGraph obj
                   every node is a cc.port obj or cc.circuit_module obj
        '''
        assert isinstance( graph, CircuitGraph)
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
            cloud.name = "cloud%d" % ccnt
            clouds.append( cloud )
        self.add_nodes_from( fds )
        self.add_nodes_from( cloud )
        
        # edges
        constfds = []
        edges = []
        for pre, succ, data in graph.edges_iter(data = True ):
            port_pair = data['port_pair']
            preport = port_pair[0].name
            succport = port_pair[1].name
            credge = ()

            #两个D触发器相连接
            if isfd( pre ) and isfd( succ):
                if (preport not in  CloudRegGraph.REMAIN_FD_PORT)\
                    or (succport not in CloudRegGraph.REMAIN_FD_PORT):
                    continue
                empty = nx.DiGraph()
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
               
        self.add_edges_from( edges)
        self.remove_nodes_from( constfds )
        self.fds = [node for node in self.nodes() if isfd(node) ]
        self.constfds = constfds
        self.clouds = clouds

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
                raise Exception, err
        return credge

    def __merge(self):
        print "----------------------------"
        print "Before_merge"
        print nx.info(self)
        print "----------------------------"
        for fd in self.fds:
            succs = self.successors( fd)
            if len(succs ) <= 1:
                continue
            else:
                big_cloud = nx.union_all(succs)
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
            if self.out_degree(fd) != 1 or self.in_degree(fd) != 1:
                err = "Error: %s indegree:%d outdegree:%d" %\
                    (fd, self.in_degree(fd), self.out_degree(fd) )
                raise Exception, err 

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
        if remain_reg != len(self.fds):
            err = "Error: %d/%d fd remains in crgraph" % (remain_reg, len(fds))
            raise Exception, err 
        self.arc = arc

def isfd( node):
    if isinstance(node, cc.circut_module) and node.m_type == 'FD':
        return True
    return False

def isvccgnd(node):
    if isinstance(node ,cc.circut_module ) and node.cellref in ['GND', "VCC"]:
        return True
    return False
    
def main(path):
    '''从目录来提取其中的每一个网表的CR图的信息
    '''
    opath = os.path.join(path, "graphpic")
    if not os.path.exists(opath):
        os.mkdir( opath )
    for eachVm in vm_files(path):
        inputfile =os.path.join(path, eachVm)
        g2 = get_graph( inputfile )
        g2.info()
        cr2 = CloudRegGraph(g2) 
        print nx.info(cr2)
        cr3 = old.CloudRegGraph(g2)
        print nx.info(cr3)

if __name__ == '__main__':
    print u"Usage:输入一个目录，将该目录下的所有.v或者。vm文件的进行crgraph建模"
    path = raw_input("plz set working directory:")
    main(path)
