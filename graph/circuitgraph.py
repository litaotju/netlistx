# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 22:31:02 2015
@author: litao
@e-mail:litaotju@qq.com
address:Tianjin University
"""
import os
import time
import re
import traceback

import networkx as nx
import matplotlib.pyplot as plt

# user-defined module
import netlistx.circuit as cc
import netlistx.netlist_util as nu
import netlistx.netlist_rules as nr

from netlistx import vm_parse
from netlistx.netlist import Netlist
from netlistx.exception import *
from netlistx.log import logger

__all__ = [ "CircuitGraph", "get_graph" ]

class CircuitGraph(nx.DiGraph):
    '''
       This class is a sonclass of nx.DiGraph
       Property new added :
           self.include_pipo self.vertex_set, self.edge_set
       Node attr :
           node_type ,which is a cellref or the port_type if node is pipo
           name , which is the module.name or port.port_name
       Edge attr :
           connection, which is the string of wire signal name which connect prim
           port_pair,  which records the port instance pair
    '''
    #边的属性的键名
    EDGE_ATTR_PORT_PAIRS = "port_pairs"
    EDGE_ATTR_CONNECTIONS = "connections"

    def __init__(self, netlist, include_pipo = True):
        '''@param:
                netlist, an instance of netlistx.netlist.Netlist class 
                include_pipo, a boolean variable
        '''
        assert isinstance( netlist, Netlist)
        nx.DiGraph.__init__(self)
        logger.debug( "Job: getting CircuitGraph...")
        self.name = netlist.m_list[0].name
        self.m_list = netlist.m_list
        self.assign_list = netlist.assigns
        self.include_pipo = include_pipo

        # vertexs containers 
        self.prim_vertex_list = []
        self.pipo_vertex_list = []
        self.vertex_set = []

        # edges containners
        self.prim_edge_list = []
        self.pi_edge_list = []
        self.po_edge_list = []
        self.edge_set = []
        
        #下面的两个函数会从 m_list和assign list中提取出和图连接相关的所有信息，
        #并为vertex containers 和edges containers赋值
        self.__add_vertex_from_m_list()
        self.__get_edge_from_prim_list()
        self.cloud_reg_graph = None
        self.s_graph = None
        if include_pipo: self.consistency_check()
        logger.debug( "Job: CircuitGraph get. OK!\n")

    def __add_vertex_from_m_list(self):
        logger.debug( "Process: searching the vertex of graph from m_list..." )
        pipo_vertex_list=[]
        prim_vertex_list=[]
        vertex_set=[]
        ###########################################################################
        #vertex
        prim_vertex_list = self.m_list[1:]
        for eachPrim in self.m_list[1:]:
            # assert eachPrim.cellref not in ['DSP48','DSP48E1','DSP48E'],\
            #     "CircuitGraph Error: %s found %s " % (eachPrim.cellref, eachPrim.name)
            self.add_node(eachPrim, node_type = eachPrim.cellref, name = eachPrim.name)
        if self.include_pipo:
            tmplist = self.m_list[0].port_list
            for pipo in tmplist:
                # 将多位端口分解成多个一位端口，加入到图中
                for eachPipo in pipo.split():
                    pipo_vertex_list.append( eachPipo )
                    self.add_node(eachPipo, node_type = eachPipo.port_type, name = eachPipo.name)
        vertex_set = prim_vertex_list + pipo_vertex_list

        self.prim_vertex_list = prim_vertex_list
        self.pipo_vertex_list = pipo_vertex_list
        self.vertex_set = vertex_set
        return None
    #------------------------------------------------------------------------------

    def __get_edge_from_prim_list(self):
        u''' 从prim_list当中获得边的连接的信息。
            如果self.include_pipo为真，此函数不仅将与PIPO相连接的边加入到生成的图中
            而且将为生成的CircuitGraph对象增加self.pi_edge_list和self.po_edge_list
            不论self.include_pipo为真与否，都会增加self.prim_edge_list和self.edge_set
        '''
        piname = {} #PI　instances dict keyed by name
        poname = {} #PO  instances dict keyed by name
        for primary in self.pipo_vertex_list:
            string = primary.port_assign.string
            if primary.port_type == 'input':
                piname[string] = primary
                continue
            elif not primary.port_type == 'output':
                logger.error( "Error :found an primary port neither input nor output ")
                logger.error( "       %s %s" % (primary.name, primary.port_type) ) 
                raise CircuitGraphError
            poname[string] = primary

        pi_dict = {}  # pi_dict[wire1] = {'source':pi,'sink':[]}
        po_dict = {}  # po_dict[wire1] = {'source':(),'sink':po }
        cnt_dict = {} # cnt_dict[wire1] = {'source':(),'sink':[(prim,port),()...]}
        self.__cnt_dict(pi_dict, po_dict, cnt_dict, piname, poname)
        if self.assign_list :
            self.__assign_handle(pi_dict, po_dict, cnt_dict, piname, poname)
        else:
            logger.debug( "No assignment in graph constructing." )
        self.__edges_cnt(pi_dict, po_dict, cnt_dict)

    def __cnt_dict(self, pi_dict, po_dict, cnt_dict, piname, poname):
        u'''从prim的每一个端口连接中获取连接信息
        '''
        logger.debug( "Process: searching edges from prim_vertex_list...")
        for eachPrim in self.prim_vertex_list:
            for eachPort in eachPrim.port_list:
                #assert每一个端口里面的wire都是单比特信号
                if not eachPort.port_width == 1:
                    logger.error( " >1 bitwidth signal found in %s %s"\
                        % (eachPrim.name, eachPort.port_name) )
                    raise CircuitGraphError
                # a bit wire is the format : .string = .name[.bit_loc]
                wire = eachPort.port_assign.string    # 全名 = 名称[n]

                # 如果这个信号是包含在PI名字里面
                if  piname.has_key(wire):
                    if not pi_dict.has_key(wire):
                        pi_dict[wire] = {'source':piname[wire],'sink':[]}
                    if not eachPort.port_type in ['input','clock']:
                        logger.error( "PI %s connect to Prim's Non-input Port: %s %s"\
                            % (wire, eachPrim.name, eachPort.port_name) )
                        raise CircuitGraphError
                    pi_dict[wire]['sink'].append( (eachPrim, eachPort) )
                    continue

                # 如果这个信号的名字包含在PO名字里面
                if poname.has_key(wire):
                    # 无论如何将PO中的信号全部加入到cnt_dict的信息中，之后将没有prim sink的那些信号进行过滤
                    if not cnt_dict.has_key(wire):
                        cnt_dict[wire] = { 'source':(),'sink':[] }
                    if eachPort.port_type == 'output':
                        assert not cnt_dict[wire]['source'], "%s has more than one source"
                        cnt_dict[wire]['source'] = (eachPrim, eachPort)
                    else:
                        cnt_dict[wire]['sink'].append( (eachPrim, eachPort) )
                    # 将这个信号的连接信息加入到po_dict中
                    if eachPort.port_type == "output":
                        if not po_dict.has_key(wire):
                            po_dict[wire] = {'source':(eachPrim, eachPort),'sink':poname[wire]}
                        else: #有别的输出端口已经连接到这个属于po的wire上，直接报错
                            #if po_dict[wire]['source']: #如果这个PO的bit位信号，已经有source了
                            logger.error( "wire: PO %s has more than 1 source. 1st source is %s %s.2nd source is %s %s"\
                                % (wire, po_dict[wire]['source'][0].name,po_dict[wire]['source'][1].port_name,\
                                   eachPrim.cellref, eachPrim.name) )
                            raise CircuitGraphError
                    #po_dict[wire]['source'] = (eachPrim, eachPort)
                    continue

                ## 规则检查 如果当前端口的类型是Clock，而且图包含PIPO，那么Clock必须连接在PIPO上
                #if eachPort.port_type == 'clock' and self.include_pipo :
                #    clock = eachPort.port_assign.string
                #    assert piname.has_key(clock), "Clock:%s has no connect to PI" % clock
                #    continue
                if eachPort.port_type == "clock":
                    continue

                # 如果这个信号的名字既没包含在PI也没包含在PO,那只能是Prim之间的连接了
                if not cnt_dict.has_key(wire):
                    cnt_dict[wire] = {'source':(),'sink':[] }
                if eachPort.port_type == 'output':
                    if cnt_dict[wire]['source']: #如果这个信号已经有一个source了
                        logger.error( "wire: %s has more than 1 source.1st source is %s %s .2nd source is %s %s"\
                            % (wire, cnt_dict[wire]['source'][0].name, cnt_dict[wire]['source'][1].port_name,\
                               eachPrim.cellref, eachPrim.name) )
                        raise CircuitGraphError
                    cnt_dict[wire]['source'] = (eachPrim, eachPort)
                    continue
                if eachPort.port_type == 'input':
                    cnt_dict[wire]['sink'].append( (eachPrim, eachPort) )
                    continue
                # 如果运行到这里了，说明当前这个wire什么也没有连接到
                logger.error( "wire cnt to neither input nor output port. %s %s %s"\
                    % (eachPrim.name ,eachPort.name, eachPort.port_type) )
                raise CircuitGraphError
        return None

    def __assign_handle(self, pi_dict, po_dict, cnt_dict, piname, poname):
        u'''处理assign语句，补全电路的连接信息。assign的左边等于 target wire，右边等于 driver wire
            处理的原则是寻找target wire 的source，让其等于driver wire 的source
            顺便让driver wire的sink 附加上 target的sink。（！千万不能等于） 在电路中如果存在一个多扇出的状况的话。
        '''
        logger.debug( "Process: handing assignment for connection...")
        # step1.首先检查assign语句的合法性。规则见注释
        #       其次合并冗余的赋值，使每一个target真正对应于某一个driver.
        assign_dict = {}
        for assign in self.assign_list:
            assert isinstance(assign, cc.assign), str(assign.__class__)
            left = assign.left_signal
            right = assign.right_signal
            l = left.string
            r = right.string
            # rule1. GND VCC的右值
            if l == "GND": 
                assert r == "1'b0"
                continue
            if l == "VCC":
                assert r == "1'b1"
                continue

            # rule2. 宽度必须为1
            assert left.width == 1,  "Error: assign leftwidth  >1 explicitly. %s" % assign
            assert right.width == 1, "Error: assign rightwidth >1 explicitly. %s " % assign
            
            # rule3. 即是凡是assign中出现了pi po相关的信号，都必须保证这个pi或者po本身是单比特的。且赋值中是单比特的形式
            assert not piname.has_key(left.name) , "Error: input beeing assigned: %s" % assign
            if poname.has_key(left.name):
                assert left.vector == None, "A vector po beeing assigned Explicitly: %s" %assign
                assert poname[left.name].port_assign.vector == None, "A vector po beeing assigned: %s" %assign
            if piname.has_key(right.name):
                assert right.vector == None,"A vector pi being driver Explicitly %s" % assign
                assert piname[right.name].port_assign.vector == None, "A vector pi being driver: %s" % assign
            if poname.has_key(right.name):
                assert right.vector == None, "A vector po being driver Explicitly %s" % assign
                assert poname[right.name].port_assign.vector == None,  "A vector po being driver: %s" % assign
            
            # rule4. 不能重复的assign一个信号
            assert not assign_dict.has_key(l), \
                "Leftvalue:%s has been assigned more than once." % l
            assign_dict[l] = r
        
        # step2. 追溯连环的assign,让其等于真正的driver
        all_l = assign_dict.keys()
        for l in all_l:
            r = assign_dict[l]
            while(assign_dict.has_key(r)):
                assign_dict[l] = assign_dict[r]
                r = assign_dict[r]
        
        # step3. 将target和driver分别加入到3种连接字典中。
        for assign in self.assign_list:
            target = assign.left_signal.string
            if target in ["GND", 'VCC']:
                continue
            driver = assign_dict[target]
            # 如果这个terget是一个PO
            if poname.has_key(target):
                assert not po_dict.has_key(target),"A po is drived by two nets"
                po_dict[target] = {'source':(), "sink": poname[target]}
                if piname.has_key(driver):
                    #print "Waing:A pi has been connected to PO directly"
                    po_dict[target]['source'] = ( piname[driver], piname[driver] )
                    if not pi_dict.has_key(driver):
                        #没有任何一个prim的端口列接到右值的这个PI上
                        pi_dict[driver] = {'source':piname[driver], "sink" :[]}
                    pi_dict[driver]['sink'].append( (poname[target], poname[target]) )
                elif cnt_dict.has_key(driver):
                    po_dict[target]['source'] = cnt_dict[driver]['source']
                else:
                    logger.error( "assignment \" %s \" is illegal.Left wire is not effectively drived" % assign )
                if cnt_dict.has_key(target):
                    # 如果某一个prim的输入连接到这个terget上了，那么要判断tergte的source类型来决定
                    # 这个连接是属于pi_dict管理的范畴还是cnt_dict涵盖的范畴，两个不能兼容
                    source = po_dict[target]['source'] # a tuple
                    if isinstance(source[0], cc.port):
                        pi_dict[driver]['sink'] += cnt_dict[target]['sink']
                        del cnt_dict[target]
                    else:
                        cnt_dict[target]['source'] = source
                continue
            
            # 如果这个terget是一个非PO的wire
            elif cnt_dict.has_key(target):
                # 如果一个target _ wire需要在assign里面进行赋值，那它一定是因为本身没有驱动
                assert not cnt_dict[target]['source']
                if piname.has_key(driver):
                    if not pi_dict.has_key(driver):
                        # 这个driver没有连接到其他的prim上
                        pi_dict[driver] = {'source':piname[driver], 'sink':[]}
                    pi_dict[driver]['sink'] += cnt_dict[target]['sink']
                    del cnt_dict[target]
                elif cnt_dict.has_key(driver):
                    cnt_dict[target]['source'] = cnt_dict[driver]['source']
                    cnt_dict[driver]['sink'] += cnt_dict[target]['sink']
                else:
                    logger.error( "assignment \" %s \" is illegal" % assign )
                continue
            # 如果这个terget即不是po也不存在prim wire里面。那么说明这个target可能只是为了进行assign的传递。
            else:
                logger.warning( "assignment \" %s \" maybe illegal check it." % assign )

    def __edges_cnt(self,  pi_dict, po_dict, cnt_dict):
        u'''@brief:
                从这三个字典中提取所有所有的边，加入到DiGraph的属性中。
            @param:
                pi_dict = {}  # pi_dict[pi_wire_name] = {'source':pi,'sink':[]}
                po_dict = {}  # po_dict[po_wire_name] = {'source':(),'sink':po }
                cnt_dict = {} # cnt_dict[wire] = {'source':(),'sink':[(prim,port),()...]}
        '''
        # ------------------------------------------------------------------------
        # prim_edge的找出
        for eachWire, SourceSinkDict in cnt_dict.iteritems():
            source = SourceSinkDict['source']
            sinks = SourceSinkDict['sink']
            if not source:
                if self.include_pipo : 
                    logger.warning( "no source of signal %s " % eachWire )
                # raise CircuitGraphError
                continue
            if len(sinks) < 1 :
                # GND VCC 的输出可能不会连接到其他PRIM上，所以其sink可以为0
                if source[0].cellref in ['VCC', 'GND']:
                    continue
                #print "Waring: %s has no prim sink ,its source is %s %s %s"%\
                #    (eachWire, source[0].cellref, source[0].name, source[1].port_name)
                #continue
            for eachSink in sinks:
                self.add_medge(source[0], eachSink[0],\
                    port_pair = (source[1], eachSink[1]),\
                    connection = eachWire)
                prim_edge = [ [source[0], eachSink[0]],[source[1], eachSink[1]], eachWire ]
                self.prim_edge_list.append(prim_edge)

        # 如果不包含PIPO，那么现在就退出函数，不将与PIPO相连接的边加入到图中
        if not self.include_pipo:
            self.edge_set = self.prim_edge_list
            logger.info( "Note: get all edges succsfully, WARING : NO PIPO EDGES IN GRAPH" )
            return None
        # ------------------------------------------------------------------------
        logger.debug( "Process: searching PIPO edges from m_list...")
        for eachWire,piConnect in pi_dict.iteritems():
            source = piConnect['source']  # cc.port instance
            sinks = piConnect['sink']
            for eachSink in sinks:
                self.add_medge(source,eachSink[0],\
                              port_pair = (source,eachSink[1]),\
                              connection = eachWire)
                pi_edge = [ [source,eachSink[0]], [source, eachSink[1]],eachWire]
                self.pi_edge_list.append(pi_edge)
        for eachWire, poConnect in po_dict.iteritems():
            source = poConnect['source'] # a tuple (prim, port)
            sink = poConnect['sink']   #cc.port instance
            self.add_medge(source[0], sink,\
                          port_pair = (source[1], sink),\
                          connection= eachWire)
            po_edge = [ [source[0], sink], [source[1], sink], eachWire]
            self.po_edge_list.append(po_edge)
        # 将所有的Edge合并到self.edge_set属性当中
        self.edge_set = self.pi_edge_list + self.po_edge_list + self.prim_edge_list
        logger.debug( "Note : get all the edges succsfully")
        return None

    def add_medge(self, source, sink, port_pair, connection):
        u'''@brief : 给图添加新的边（如果原来不存在），并更新边的数据
            @params:
                source: a port or a module obj
                sink : a port or a module obj
                port_pair: a tuple of (port1, port2)
                connection: a string of wire name
            @return:
                None
        '''
        if self[source].has_key(sink):
            port_pairs = self[source][sink][ CircuitGraph.EDGE_ATTR_PORT_PAIRS ]
            connections = self[source][sink][ CircuitGraph.EDGE_ATTR_CONNECTIONS ]
        else:
            port_pairs =[]
            connections = []
        port_pairs.append(port_pair)
        connections.append( connection)
        self.add_edge( source, sink, { CircuitGraph.EDGE_ATTR_PORT_PAIRS: port_pairs, 
                                       CircuitGraph.EDGE_ATTR_CONNECTIONS: connections} )

    def consistency_check(self):
        u'''根据每一个节点的输入来检查图的完整性，只能检查带有PIPO的图
            具体的方法是，如果是一个原语。原语的入度应该等于其input端口或者clock端口的数量
            如果是一个端口，input端口的入度为0，output端口的出度为0
        '''
        if not self.include_pipo:
            logger.warning( "cannot check consistency for no pipo graph")
            return None
        for node in self.nodes_iter():
            if isinstance(node, cc.circut_module):
                inports = [port for port in node.port_list if port.port_type in ('clock', 'input')]
                if not self.in_degree( node) == len( inports):
                    realinports = []
                    for pre in self.predecessors_iter(node):
                        realinports += self[pre][node][CircuitGraph.EDGE_ATTR_PORT_PAIRS]
                    if len(realinports) != len(inports):
                        errmsg = "Prim:%s %s has %d input ports,  %d been connected. indegree:%d" %\
                        (node.cellref, node.name, len(inports), len(realinports), self.in_degree(node))
                        raise AssertionError, errmsg
                    else:
                        logger.info( "node:%s %s has pre with multi connection" % (node.cellref, node.name) )
            elif isinstance(node, cc.port):
                if node.port_type == "output":
                    if  self.in_degree( node) != 1 or self.out_degree( node ) != 0 :
                        errmsg = "Port: %s %s indegree %d, outdegree %d" %\
                         (node.port_type, node.port_name, self.in_degree(node) , self.out_degree( node) )
                        raise AssertionError, errmsg
                elif  node.port_type == 'input':
                    if self.in_degree( node ) != 0 :
                        errmsg = "Port: %s %s indegree %d, outdegree %d" %\
                         (node.port_type, node.port_name, self.in_degree(node) , self.out_degree( node) )
                        raise AssertionError, errmsg

    def topo_copy( self, gcopy = None):
        if gcopy is None:
            gcopy = nx.DiGraph()
        else:
            assert isinstance(gcopy, nx.DiGraph)
            gcopy.clear()
        for edge0, edge1, data in self.edges_iter(data = True):
            gcopy.add_edge( edge0, edge1, data)
        for node in self.nodes_iter():
            gcopy.add_node( node )
        return gcopy
    #------------------------------------------------------------------------------
    def info(self, verbose = False) :
        print "\n------------------------------------------------------"
        print "module %s   CircuitGraph info: " % self.m_list[0].name
        print "pipo included : ", self.include_pipo
        print nx.info(self)
        if verbose:
            print "Info :%d nodes in graph. Node Set Are:"% self.number_of_nodes()
            node_type = nx.get_node_attributes(self, 'node_type')
            name = nx.get_node_attributes(self, 'name')
            for eachNode in self.nodes_iter():
                print "    %s %s" % (node_type[eachNode], name[eachNode])

            print "Info :%d edges in graph. Edge Set Are:"% self.number_of_edges()
            connection = nx.get_edge_attributes(self, 'connection')
            port_pair = nx.get_edge_attributes(self, 'port_pair')
            for eachEdge in self.edges_iter():
                print "    (%s -> %s):(wire %s, port:%s->%s)" % \
                (eachEdge[0].name,eachEdge[1].name,connection[eachEdge]\
                ,port_pair[eachEdge][0].name,port_pair[eachEdge][1].name)
        print "------------------------------------------------------"
    
    def paint(self):
        u''' 给电路图，分组画出来，不同的颜色和标签标明了不同的prim '''
        label_dict={}
        fd_list  = []
        pipo_list= []
        others   = []
        for eachVertex in self.nodes_iter():
            if isinstance(eachVertex, cc.circut_module):
                label_dict[eachVertex] = eachVertex.cellref + " : " + eachVertex.name
                if eachVertex.m_type == 'FD':
                    fd_list.append(eachVertex)
                else:
                    others.append(eachVertex)
            else:
                assert isinstance(eachVertex, cc.port)
                label_dict[eachVertex] = eachVertex.port_type + \
                    " : " + eachVertex.port_name
                pipo_list.append(eachVertex)
        ps = nx.spring_layout(self)
        if self.include_pipo:
            nx.draw_networkx_nodes(self,pos=ps,nodelist=pipo_list,node_color='r')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=others,node_color='b')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=fd_list,node_color='g')
        nx.draw_networkx_edges(self,ps)
        nx.draw_networkx_labels(self,ps,labels=label_dict)
        plt.savefig("test_output\\"+self.m_list[0].name+"_original_.png")
        return None
        
    def to_gexf_file(self, filename):
        u'''把图写入gexf文件，不对原图做任何改变
            新图中的节点增加了id和label两个属性
        '''
        new_graph = nx.DiGraph()
        for node in self.nodes_iter():
            node_label = node.cellref if isinstance(node, cc.circut_module) else node.port_type
            node_id = '_d_'+node.name[1:] if node.name[0]=='\\' else node.name
            new_graph.add_node(node, id= node_id, label = node_label)
        for start, end, data in self.edges_iter(data=True):
            #label = data['connection']
            new_graph.add_edge(start, end)
        try:
            nx.write_gexf(new_graph, filename)
        except Exception, e:
            traceback.print_exc()
            logger.warning( "can not write gexf file correctly: %s", e)

    def to_dot_file(self, filename):
        u'''把图写入到dot文件中，不对原图做什么改变
            新图的节点只是字符串。
        '''
        new_graph = nx.DiGraph()
        for start, end, data  in self.edges_iter(data = True):
            port_pair = data[ CircuitGraph.EDGE_ATTR_PORT_PAIRS]
            connection = data[CircuitGraph.EDGE_ATTR_CONNECTIONS]
            edge = [start, end] # 存储边的起点和终点
            node_id =['','']    # 存储节点的名称
            node_data =[{},{}]  # 存储要打印到dot中的信息
            for i in range(2):
                # 当前节点是prim 或者是 port
                is_prim = True if isinstance(edge[i], cc.circut_module) else False
                # prim和port的数据属性不同，根据判断为生成dot节点的名称，和节点附属的['shape']数据
                node_name = '_d_'+edge[i].name[1:] if edge[i].name[0]=='\\' else edge[i].name 
                node_id[i] = edge[i].cellref+node_name if is_prim else\
                             edge[i].port_type+node_name
                # prim为box形状（盒子），port为invtriangle形状（倒三角）
                node_data[i]['shape'] = 'box' if is_prim else 'invtriangle' 
                new_graph.add_node(node_id[i],node_data[i])
            new_graph.add_edge(node_id[0], node_id[1])
        try:
            nx.write_dot(new_graph, filename)
        except Exception, e:
            traceback.print_exc()
            logger.warning( "Cannot write dot file %s" % e)

#------------------------------------------------------------------------------
        
def get_graph(fname = None):
    u'''@param: fname, a vm file name
       @return: g1, a nx.DiGraph obj
       @brief: 从文件名获得一个图
    '''
    if not fname: fname = raw_input("plz enter file name:")
    assert( os.path.exists( fname ) )
    info = vm_parse( fname )
    netlist    = Netlist(info)
    #nr.check(netlist, check_reset = False)
    g1 = CircuitGraph(netlist)
    return g1
    
def save_graphs(fname, path):
    u'''@brief：输入一个文件名，生成带PIPO和不带PIPO的图，然后将生成的图分别保存到path下的.dot文件和.gexf文件
       @params:
            fname, a string
            path,  a path(will make a new path if not existed)
       @return: none
    '''
    info = vm_parse(fname)
    netlist = Netlist( info )

    #如果网表中模块数量小于等于20个，则逐个打印模块的信息，方便手动检查
    if len(netlist.m_list) <= 20:
        logger.info( "\n".join( [str(eachPrim) for eachPrim in netlist.m_list] ) )
        verbose_info =True
    else:
        verbose_info = False
        logger.info( "The m_list is too long >20. ignore..." )
    
    #生成保存图的路径
    if not os.path.exists( path):
        os.makedirs( path )
    
    #生成带pipo的图
    g1 = CircuitGraph(netlist, include_pipo = True)
    g1.info(verbose_info)
    g1.to_gexf_file(path + '\\%s_icpipo.gexf' % g1.name)
    g1.to_dot_file( path + "\\%s_icpipo.dot" % g1.name)
    
    #生成不带pipo的图
    g2 = CircuitGraph(netlist, include_pipo = False)
    g2.info(verbose_info)
    g2.to_gexf_file( path + "\\%s_nopipo.gexf" % g2.name)
    g2.to_dot_file( path +  "\\%s_nopipo.dot" % g2.name)
    return None

def fanout_stat(graph):
    '''统计图中的FD节点和组合逻辑节点的扇出，打印到标准输出上
    '''
    g1 = graph #local variable
    com_degree_stat = {} #组合逻辑扇出的统计
    fd_degree_stat = {}  #D触发器扇出数量的统计
    for eachNode in g1.nodes_iter():
        degree = g1.out_degree(eachNode)
        if isinstance(eachNode, cc.circut_module):
            if eachNode.m_type != 'FD':
                if not com_degree_stat.has_key( degree ):
                    com_degree_stat[degree] = 0
                com_degree_stat[ degree] += 1
            else:
                if not fd_degree_stat.has_key( degree ):
                    fd_degree_stat[degree]  =0
                fd_degree_stat[degree] += 1
    print "combinational node degree are:"
    print "outdegree node_count"
    for key, val in com_degree_stat.iteritems():
        print "%d     %d" % (key, val)
    print "fd node degree stat are:"
    print "outdegree node_count"
    for key ,val in fd_degree_stat.iteritems():
        print "%d      %d" % (key, val)
    return fd_degree_stat, com_degree_stat
