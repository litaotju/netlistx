# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
class  circuit_graph
"""
import networkx as nx
import matplotlib.pyplot as plt
import class_circuit as cc
from graph_s_graph import s_graph
###########################################################################
class circuit_graph(nx.DiGraph):
    '''This class is a sonclass of nx.DiGraph and construct with a m_list[]
       Property new added :
           self.include_pipo self.vertex_set,self.edge_set
       Node attr :
           node_type ,which is a cellref or the port_type if node is pipo
           name , which is the module.name or port.port_name
       Edge attr :
           connection,which is the string of wire signal name which connect prim
           port_pair, which records the port instance pair
    '''
    
    def __init__(self,m_list,include_pipo=False):
        nx.DiGraph.__init__(self)
        self.m_list=m_list
        self.include_pipo=include_pipo
        self.__add_edge_vertex_from_m_list__(m_list,self.include_pipo)
        self.cloud_reg_graph=None
        self.s_graph=None
        print "Note: circuit_graph() build successfully"
    def __add_edge_vertex_from_m_list__(self,m_list,include_pipo):
        '''
            now we cannot handle the graph construction problem with concering DSP
            because, in hardware fault injection emulaiton process, when signal passing 
            DSP, we cannot compute the signal correctly
        '''
        print "Process: gu.circuit_graph()..searching the vertex and edges of netlist..."
        pipo_vertex_list=[]
        prim_vertex_list=[]
        vertex_set=[]
        
        pi_edge_list=[]
        po_edge_list=[]
        prim_edge_list=[]
        edge_set=[]
        ###########################################################################
        #vertex
        prim_vertex_list=m_list[1:]
        for eachPrim in m_list[1:]:
            assert eachPrim.cellref not in ['DSP48','DSP48E1','DSP48E'],"DSP found %s "%eachPrim.name
            self.add_node(eachPrim,node_type=eachPrim.cellref,name=eachPrim.name)
        if include_pipo:
            pipo_vertex_list=m_list[0].port_list
            for eachPipo in pipo_vertex_list:
                self.add_node(eachPipo,node_type=eachPipo.port_type,name=eachPipo.name)
        vertex_set=prim_vertex_list+pipo_vertex_list
        ###########################################################################
        #edge
        #edge_set的每一个元素是 一个([],[],{})类型的变量,
        #第一个列表存储prim,第二个存储port,第三个存储连接信号
        #---------------------------pipo edge ------------------------------------           
        if include_pipo:
            print "Process: searching PI and PO edges..."
            for eachPrim in prim_vertex_list:
                for eachPort in eachPrim.port_list:
                    for eachPPort in pipo_vertex_list:
                        cnt_flag=False
                        #信号名称等于端口名称,可能prim port的信号是Pipo的某一bit
                        if isinstance(eachPort.port_assign,cc.signal) and \
                                eachPort.port_assign.name==eachPPort.port_name:
                            connection=eachPort.port_assign.name
                            cnt_flag=True                    
        #                elif isinstance(eachPort.port_assign,cc.joint_signal):
        #                    for eachSubsignal in eachPort.port_assign.sub_signal_list:
        #                        if eachSubsignal.name==eachPPort.port_name:
        #                            cnt_flag=True
        #                            break
        #                        else:
        #                            continue
                        if cnt_flag:
                            if eachPPort.port_type=='input':
                                assert eachPort.port_type in ['input','un_kown','clock'],\
                                    (":port:%s,port_type:%s"%(eachPort.port_name,eachPort.port_type))
                                pi_edge_list.append([[eachPPort,eachPrim],[eachPPort,eachPort],connection])
                            else:
                                ##只有输prim 的输出端口 才能连接到po port上。否则只是PO的反馈，一定在Primedge中存在
                                if eachPort.port_type=='output':
                                    po_edge_list.append([[eachPrim,eachPPort],[eachPort,eachPPort],connection])
        print "Process: searching Prim edges..."        
        #---------------------------prim edge --------------------------------------------   
        for eachPrim in prim_vertex_list:
            for eachPrim2 in prim_vertex_list:
                if eachPrim2==eachPrim:
                    continue
                else:
                    p_set=set(eachPrim.port_assign_list)
                    p_set2=set(eachPrim2.port_assign_list)
                    if p_set.intersection(p_set2):
                        for eachPort in eachPrim.port_list:
                            for eachPort2 in eachPrim2.port_list:
                                if eachPort2.port_assign.string==eachPort.port_assign.string and\
                                        eachPort2.port_type!=eachPort.port_type:
                                    connection=eachPort2.port_assign.string
                                    if eachPort.port_type=='input':
                                        tmp_edge=[[eachPrim2,eachPrim],[eachPort2,eachPort],connection]
                                        prim_edge_list.append(tmp_edge)
                                    else:
                                        tmp_edge=[[eachPrim,eachPrim2],[eachPort,eachPort2],connection]
                                        prim_edge_list.append(tmp_edge)
        #--------merge all the edge-------------------------------------------------------
        edge_set=pi_edge_list+po_edge_list+prim_edge_list
        self.prim_vertex_list=prim_vertex_list
        self.pipo_vertex_list=pipo_vertex_list
        self.vertex_set=vertex_set
        #注意，prim_edge_list由于其搜索方法的限制，所以其长度是实际边数目的两倍
        self.prim_edge_list=prim_edge_list
        self.edge_set=edge_set
        
        for eachEdge in edge_set:
            self.add_edge(eachEdge[0][0],eachEdge[0][1],\
            connection=eachEdge[2],port_pair=eachEdge[1])
            
    #------------------------------------------------------------------------------   
    def info(self,verbose=False) :
        print "Circuit graph info:"
        print nx.info(self)
        if verbose:
            print "Info :%d nodes in graph. Node Set Are:"% self.number_of_nodes()        
            for eachNode in self.nodes_iter():
                node_type=nx.get_node_attributes(self,'node_type')
                name=nx.get_node_attributes(self,'name')
                print "    %s %s"%(node_type[eachNode],name[eachNode])
            print "Info :%d edges in graph. Edge Set Are:"% self.number_of_edges()
            for eachEdge in self.edges_iter():
                connection=nx.get_edge_attributes(self,'connection')
                port_pair =nx.get_edge_attributes(self,'port_pair')
                print "    (%s -> %s):(wire %s, port:%s->%s)"% \
                (eachEdge[0].name,eachEdge[1].name,connection[eachEdge]\
                ,port_pair[eachEdge][0].name,port_pair[eachEdge][1].name)
        return True
    #------------------------------------------------------------------------------   
    def paint(self):
        label_dict={}
        for eachVertex in self.nodes_iter():
            if isinstance(eachVertex,cc.circut_module):
                label_dict[eachVertex]=eachVertex.cellref+" : "+eachVertex.name
            else:
                assert isinstance(eachVertex,cc.port)
                label_dict[eachVertex]=eachVertex.port_type+\
                    " : "+eachVertex.port_name
        ps=nx.spring_layout(self)
        fd_list  =[]
        pipo_list=[]
        others   =[]
        for eachNode in self.nodes_iter():
            if isinstance(eachNode,cc.circut_module) and eachNode.m_type=='FD':
                fd_list.append(eachNode)
            elif isinstance(eachNode,cc.port):
                pipo_list.append(eachNode)
            else:
                others.append(eachNode)
        if self.include_pipo:
            nx.draw_networkx_nodes(self,pos=ps,nodelist=pipo_list,node_color='r')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=others,node_color='b')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=fd_list,node_color='g')
        nx.draw_networkx_edges(self,ps)
        nx.draw_networkx_labels(self,ps,labels=label_dict)
        plt.savefig(self.m_list[0].name+"_original_.png")
        return True
        
##———————————————————————————————————————————————————————————————————————————————————————
    #featured 7.13        
    ###progressing the cloud and registerize the original circuit graph
    def get_cloud_reg_graph(self):
        ''' 
            -->>self.cloud_reg_graph.copy()
            Model the circuit graph to a cloud(combinational cone) and register(FD)
            graph,add a .cloud_reg_graph data to self.
            注意：1.现有的cloud_register图中没有包含pipo节点，只是prim的节点
                 2.函数不仅为调用它的对象增加了一个 cloud_reg_graph数据，最终返回了该图的深度复制
            待续：现有的算法是先去掉所有的FD，将剩下的连通分量合并成一个cloud。实际上如果剩下的图不
                连通，那么它们在电路中可以合并成一个子图吗?
        '''
        #g2是一个用self中的点和边建立的无向图，所以基本的节点和self的节点是完全一致的，
        #每一个节点都指向了m_list当中的原语的  cc.circuit_module() 对象的实例化
        print "Process: func get_cloud_reg_graph()"
        g2=nx.Graph()
        g2.add_nodes_from(self.prim_vertex_list)
        for eachEdge in self.prim_edge_list:
            g2.add_edge(eachEdge[0][0],eachEdge[0][1])

        #------------------------------------------------------
        #step1 找出FD节点，并移去FD节点
        fd_list=[]
        for eachFD in self.prim_vertex_list:
            if eachFD.m_type=='FD':
                fd_list.append(eachFD)
        g2.remove_nodes_from(fd_list)
        
        #------------------------------------------------------
        #step2 找出连通分量,建立子图
        l1=[]
        cc=nx.connected_components(g2)
        for c in cc:
            ccsub=g2.subgraph(c)
            l1.append(ccsub)
        #print "Info:%d connected_componenent subgraph after remove FD"%len(l1)
        #step2.1 将每一个连通分量，也就是子图恢复为有向图，这样做的目的是搞清楚组合逻辑之间的连接关系
        #由于不存在组合逻辑回路，所以理论上，将全是组合的子图转换成有向图，边的数目完全相等
        #这可以通过下面的打印信息来查看
        #l2是L1的有向图版
        l2=[]        
        for eachSubgraph in l1:
#            print "before:"
#            print nx.info(eachSubgraph)
            h=nx.DiGraph(eachSubgraph)
            if eachSubgraph.number_of_nodes()>1:
                for eachEdge in h.edges():
#                    cores_node0=vertex_in_graph(eachEdge[0],self)
#                    cores_node1=vertex_in_graph(eachEdge[1],self)
#                    if not self.has_edge(cores_node0,cores_node1):
                    if not self.has_edge(eachEdge[0],eachEdge[1]):
                        h.remove_edge(eachEdge[0],eachEdge[1])
            l2.append(h)
#            print "after:"
#            print nx.info(h)

        
        
        #------------------------------------------------------
        #step3 记录下fd的D Q 端口与其他FD以及 与组合逻辑的有向边，以及节点
        special_edges=[]
        reg_reg_edges=[]
        fd_linked_nodes_edges={}
        for x in self.prim_edge_list:
           for eachNode in x[0]:
               if eachNode.m_type=='FD':
                  tmp= 1 if x[0].index(eachNode)==0 else 0
                  fd_port=x[1][1-tmp] #记录下来现在的FD的端口
                  other_prim=x[0][tmp]
                  other_port=x[1][tmp] 
                  if (other_prim.m_type!='FD') and (fd_port.name in ['D','Q']):
                      non_fd_prim=other_prim
                      if not fd_linked_nodes_edges.has_key(non_fd_prim):
                          fd_linked_nodes_edges[non_fd_prim]=[]
                      fd_linked_nodes_edges[non_fd_prim].append(x)
                  elif other_prim.m_type=='FD' and (fd_port.name in ['D','Q'] ) and\
                      other_port.port_name in ['D','Q']:
                      reg_reg_edges.append(x)
                  else:
                      special_edges.append(x)
                      
        #------------------------------------------------------
        #step4 
        #新建一个有向图，节点为 cloud（step2获得的连通分量）+fd（step1获得）
        #              边为fd-cloud的有向连接（step3获得）
        g3=cloud_reg_graph()
        g3.add_clouds_from(l2)
        g3.add_regs_from(fd_list)
        for eachSubgraph in l2: 
            for eachNonFdPrim in fd_linked_nodes_edges.keys():
                #if vertex_in_graph(eachNonFdPrim,eachSubgraph):
                if eachSubgraph.has_node(eachNonFdPrim):
                    tmp_edge_list=fd_linked_nodes_edges[eachNonFdPrim]
                    for eachEdge in tmp_edge_list:
                        if eachEdge[0][0]==eachNonFdPrim:
                            ##注意，在这用等号是合法的，因为他们两都是原来的prim_vertex_set
                            ##在新添加边的时候，保留了在原图中的边的信息
                            g3.add_edge(eachSubgraph,eachEdge[0][1],original_edge=eachEdge)
                        else:
                            assert eachEdge[0][1]==eachNonFdPrim
                            g3.add_edge(eachEdge[0][0],eachSubgraph,original_edge=eachEdge)
        ##注意，在reg_reg_edges当中，边的元素，就是fd_list当中的module对象。所以这样做不会增加新的边
        for eachEdge in reg_reg_edges:
            g3.add_edge(eachEdge[0][0],eachEdge[0][1],original_edge=eachEdge)
        self.cloud_reg_graph=g3        
#        for eachNode in g3.nodes_iter():
#            print eachNode.__class__
#            if isinstance(eachNode,cc.circut_module):
#                print "%s %s "%(eachNode.cellref,eachNode.name)
        return self.cloud_reg_graph.copy()
##———————————————————————————————————————————————————————————————————————————————————————
##featured 7.16
    def get_s_graph(self):
        '''
           >>>self.s_graph.copy(),根据已有的图来生成s-graph
           生成的s图完全是nx.DiGraph类的，不是自定义类，初步评估发现，用这种方法
           生成s图比 原先graph_s_graph中的只处理边集和点集更快速。所以有必要修改
           该类的定义和构造函数。
        '''
        care_type=('FD')
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
        ##为DiGraph内核添加节点与图
        s1.add_nodes_from(self.vertex_set)
        for eachEdge in self.edge_set:
            s1.add_edge(eachEdge[0][0],eachEdge[0][1],\
                    port_pair=eachEdge[1],cnt=eachEdge[2])
        node_type_dict=nx.get_node_attributes(self,'node_type')   
        
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
                                new_edge.append(eachS,eachD)
                                s1.add_edge(eachS,eachD)
        #新添加的边
        s1.new_edges=new_edge
        self.s_graph=s1
        return s1.copy()
    
def vertex_in_graph(vertex,graph):
    '''判断一个cc.module类型的vertex是否在一个nx.Graph或者nx.DiGraph图中
        判断的标准是检查图中是否有相同.cellref 相同.name的节点，
        需要这个函数的原因是nx.connected_component_subgraphs()返回的子图是对节点的深度复制.
        返回值要么是None,要么是vertex在graph中对应的节点
    '''
    assert isinstance(vertex,cc.circut_module)
    assert isinstance(graph,(nx.DiGraph,nx.Graph))
    assert len(graph)>0
    flag=None
    for eachNode in graph.nodes_iter():
        if isinstance(eachNode,cc.circut_module):
            flag1=(eachNode.cellref==vertex.cellref)
            flag2=(eachNode.name==vertex.name)
            flag=(flag1 and flag2)
            if flag:
                return eachNode
        else:
            continue
    return flag
    
    
#--------------------------------------------------------------------------------------
class cloud_reg_graph(nx.DiGraph):
    '''
        本图的节点分为两类，一类是cloud,也就是一个有向子图。一类是reg,也就是FD primitive
        子图中有存储了关于组合逻辑节点的互联信息
    '''
    def __init__(self):
        nx.DiGraph.__init__(self)
        self.clouds=[]
        self.regs=[]
    def add_clouds_from(self,list1):
        for eachCloud in list1:
            assert isinstance(eachCloud,nx.DiGraph)
            self.clouds.append(eachCloud)
            self.add_node(eachCloud)
    def add_regs_from(self,list1):
        for eachFD in list1:
            assert isinstance(eachFD,cc.circut_module) and eachFD.m_type=='FD',eachFD.name
            self.add_node(eachFD)
            self.regs.append(eachFD)    
    def paint(self):
        label_dict={}
        for eachCloud in self.clouds:
            if eachCloud.number_of_nodes()>1:
                label_dict[eachCloud]='cloud'
            else:
                node=eachCloud.nodes()[0]
                label_dict[eachCloud]=node.cellref+":"+node.name
        for eachReg in self.regs:
            label_dict[eachReg]=eachReg.cellref+":"+eachReg.name
        ps=nx.spring_layout(self)
        nx.draw_networkx_nodes(self,pos=ps,nodelist=self.clouds,node_color='r')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=self.regs,node_color='g')
        nx.draw_networkx_edges(self,ps)
        nx.draw_networkx_labels(self,ps,labels=label_dict)
        return True
    def info(self):
        print "Cloud_Reg_graph info:-----------------"
        print nx.info(self)
        print "Number of cloud:%d "%len(self.clouds)
        print "Number of register:%d"% len(self.regs)
        print "--------------------------------------"

###featured 7.14
    def check_rules(self):
        ''' to make sure the every reg in cloud_reg_graph has just  1-indegree 
        '''
        in_dict=self.in_degree(self.regs)
        for x in list(in_dict.values()):
            if x>1:
                print "Error: check_rules failed. There are FD with %d in_degree"%x
                return False
        return True