# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 22:31:02 2015
@author: litao
@e-mail:litaotju@qq.com
address:Tianjin University
"""

import networkx as nx
import matplotlib.pyplot as plt
import class_circuit as cc
from sgraph import s_graph

#  TODO :GND和VCC 原语在图形建模中的注意事项，以及如何建模
class CircuitGraph(nx.DiGraph):
    '''
       This class is a sonclass of nx.DiGraph and construct with a m_list[]
       Property new added :
           self.include_pipo self.vertex_set,self.edge_set
       Node attr :
           node_type ,which is a cellref or the port_type if node is pipo
           name , which is the module.name or port.port_name
       Edge attr :
           connection,which is the string of wire signal name which connect prim
           port_pair, which records the port instance pair
    '''

    def __init__(self, m_list, include_pipo = False):
        nx.DiGraph.__init__(self)
        self.name = m_list[0].name
        self.m_list = m_list
        self.include_pipo = include_pipo
        self.__add_edge_vertex_from_m_list(m_list, self.include_pipo)
        self.cloud_reg_graph = None
        self.s_graph = None
        print "Note: circuit_graph() build successfully"

    def __add_edge_vertex_from_m_list(self, m_list, include_pipo):
        '''
            now we cannot handle the graph construction problem with concering DSP
            because, in hardware fault injection emulaiton process, when signal passing
            DSP, we cannot compute the signal correctly
        '''
        print "Process: searching the vertex and edges of netlist..."
        pipo_vertex_list=[]
        prim_vertex_list=[]

        pi_edge_list=[]
        po_edge_list=[]
        prim_edge_list=[]

        vertex_set=[]
        edge_set=[]
        ###########################################################################
        #vertex
        prim_vertex_list=m_list[1:]
        for eachPrim in m_list[1:]:
            assert eachPrim.cellref not in ['DSP48','DSP48E1','DSP48E'],\
                "%s found %s " % (eachPrim.cellref, eachPrim.name)
            self.add_node(eachPrim, node_type = eachPrim.cellref, name = eachPrim.name)
        if include_pipo:
            pipo_vertex_list=m_list[0].port_list
            for eachPipo in pipo_vertex_list:
                self.add_node(eachPipo, node_type = eachPipo.port_type, name = eachPipo.name)

        vertex_set = prim_vertex_list + pipo_vertex_list

        ###########################################################################
        #edge
        #edge_set的每一个元素是 一个([],[],{})类型的变量,
        #第一个列表存储prim,第二个存储port,第三个存储连接信号
        #---------------------------pipo edge ------------------------------------
        if include_pipo:
            print "    Process: searching PI and PO edges..."
            for eachPrim in prim_vertex_list:
                for eachPort in eachPrim.port_list:
                    for eachPPort in pipo_vertex_list:
                        cnt_flag=False
                        #信号名称等于端口名称,可能prim port的信号是pipo的某一bit
                        if isinstance(eachPort.port_assign, cc.signal) and \
                                eachPort.port_assign.name == eachPPort.port_name:
                            connection = eachPort.port_assign.name
                            cnt_flag = True
                        # 这一部分用于多位端口的连接
        #                elif isinstance(eachPort.port_assign,cc.joint_signal):
        #                    for eachSubsignal in eachPort.port_assign.sub_signal_list:
        #                        if eachSubsignal.name==eachPPort.port_name:
        #                            cnt_flag=True
        #                            break
        #                        else:
        #                            continue
                        if cnt_flag:
                            if eachPPort.port_type=='input':
                                assert eachPort.port_type in ['input', 'clock'],\
                                    ("%s %s  port:%s, port_type:%s"\
                                    % (eachPrim.cellref, eachPrim.name, \
                                       eachPort.port_name, eachPort.port_type))
                                pi_edge_list.append([[eachPPort,eachPrim], [eachPPort,eachPort], connection])
                            else:
                                ##只有输prim 的输出端口 才能连接到po port上。否则只是PO的反馈，一定在prim_edge中存在
                                if eachPort.port_type=='output':
                                    po_edge_list.append([[eachPrim,eachPPort], [eachPort,eachPPort], connection])
        
        print "    Process: searching Prim edges..."
        self.fd_loop = []
        #---------------------------prim edge --------------------------------------------
        for eachPrim in prim_vertex_list:
            for eachPrim2 in prim_vertex_list:
                # 存在prim与自身的连接
                p_set = set(eachPrim.port_assign_list)
                p_set2 = set(eachPrim2.port_assign_list)
                if not p_set.intersection(p_set2):
                    continue
                for eachPort in eachPrim.port_list:
                    for eachPort2 in eachPrim2.port_list:
                        sig1 = eachPort.port_assign.string
                        sig2 = eachPort2.port_assign.string
                        if sig2 == sig1 and \
                            eachPort2.port_type != eachPort.port_type:
                            if eachPrim is eachPrim2 :
                                assert eachPrim.m_type == 'FD' ,\
                                "Combinational Prim loop: %s %s" % ( eachPrim.cellref, eachPrim.name )
                                #print "        FD-self loop %s %s " % ( eachPrim.cellref, eachPrim.name )
                                self.fd_loop.append( (eachPrim , eachPort, eachPort2) )
                            connection = sig2
                            if eachPort.port_type == 'input':
                                tmp_edge = [[eachPrim2 ,eachPrim], [eachPort2, eachPort], connection]
                            else:
                                tmp_edge = [[eachPrim, eachPrim2], [eachPort ,eachPort2],  connection]
                            if tmp_edge in prim_edge_list:
                                continue
                            prim_edge_list.append(tmp_edge)
        #--------merge all the edge-------------------------------------------------------
        edge_set = pi_edge_list + po_edge_list + prim_edge_list
        self.prim_vertex_list = prim_vertex_list
        self.pipo_vertex_list = pipo_vertex_list
        self.vertex_set = vertex_set
        #注意，prim_edge_list由于其搜索方法的限制，所以其长度是实际边数目的两倍
        self.prim_edge_list = prim_edge_list
        self.edge_set = edge_set

        for eachEdge in edge_set:
            self.add_edge(eachEdge[0][0], eachEdge[0][1],\
            connection=eachEdge[2] , port_pair=eachEdge[1])
        # 
    #------------------------------------------------------------------------------

    def info(self, verbose = False) :
        print "----- module %s -- CircuitGraph info:----- " % self.m_list[0].name
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
        return True
    #------------------------------------------------------------------------------
    
    def paint(self):
        ''' 给电路图，分组画出来，不同的颜色和标签标明了不同的prim '''
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
        return True
        

    ###############################################################################
    def get_s_graph(self):
        '''
           >>>self.s_graph.copy(),根据已有的图来生成s-graph
           生成的s图完全是nx.DiGraph类的，不是自定义类，初步评估发现，用这种方法
           生成s图比 原先graph_s_graph中的只处理边集和点集更快速。所以有必要修改
           该类的定义和构造函数。
        '''
        care_type=('FD')
        ##step1
        ##无聊的初始化过程，先建一个s_graph的对象，然后直接对数据属性进行赋值
        s1=s_graph(self.include_pipo)
        s1.name=self.name
        if self.include_pipo:
            for x in self.pipo_vertex_list:
                if x.port_type=='input':
                    s1.pi_nodes.append(x)
                else:
                    s1.po_nodes.append(x)
        for fd in self.prim_vertex_list:
            if fd.m_type=='FD':
                s1.fd_nodes.append(fd)
        ##为DiGraph内核添加节点与边
        s1.add_nodes_from(self.vertex_set)
        for eachEdge in self.edge_set:
            s1.add_edge(eachEdge[0][0],eachEdge[0][1],\
                    port_pair=eachEdge[1],cnt=eachEdge[2])
        node_type_dict=nx.get_node_attributes(self,'node_type')   
        
        ##step2
        ##ignore 每一个非FD的primitive节点
        new_edge=[]
        for eachNode in self.nodes_iter():
            if node_type_dict[eachNode] not in ['input','output']:
                if eachNode.m_type not in care_type:
                    pre=[]
                    suc=[]
                    pre=s1.predecessors(eachNode)
                    suc=s1.successors(eachNode)
                    s1.remove_node(eachNode)
                    if pre and suc:
                        for eachS in pre:
                            for eachD in suc:
                                new_edge.append((eachS,eachD))
                                s1.add_edge(eachS,eachD)
        ##为新添加的边归类，
        s1.new_edges=new_edge
        self.s_graph=s1
        return s1.copy()
#------------------------------------------------------------------------------
        
def get_graph_from_raw_input():
    '''for test only'''
    import netlist_util as nu
    fname = raw_input("plz enter file name:")
    info = nu.vm_parse(fname)
    m_list = info['m_list']
    print "Top module is:"
    m_list[0].__print__()
    nu.mark_the_circut(m_list)
    nu.rules_check(m_list)
    g1 = CircuitGraph(m_list, include_pipo = True)
    return g1
    
def __test():
    '''for test only'''
    import netlist_util as nu
    fname = raw_input("plz enter file name:")
    info = nu.vm_parse(fname)
    m_list = info['m_list']
    for eachPrim in m_list:
        eachPrim.__print__()
    nu.mark_the_circut(m_list)
    nu.rules_check(m_list)
    
    g1 = CircuitGraph(m_list, include_pipo = True)
    g2 = CircuitGraph(m_list)
    print "----NO PIPO-----------"
    g2.info()
    print "----Including PIPO----"    
    g1.info()
    plt.figure("Original_Circut")
    g1.paint()
    return True
#------------------------------------------------------------------------------
if __name__ =='__main__':
    __test()

    
