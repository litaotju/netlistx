# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 22:28:45 2015
@author: litao
@e-mail:litaotju@qq.com
address:Tianjin University
"""
import copy
import networkx as nx
import class_circuit as cc
from circuitgraph import CircuitGraph
from exception import *
###############################################################################


class CloudRegGraph(nx.DiGraph):
    '''
        本图的节点分为两类，一类是cloud,也就是一个有向子图。一类是reg,也就是FD primitive
        子图中有存储了关于组合逻辑节点的互联信息
    '''
    def __init__(self, basegraph ):
        'parameter :basegraph ，a CircuitGraph Object'
        nx.DiGraph.__init__(self)
        self.basegraph = basegraph #记录原图的信息
        self.clouds=[]
        self.regs=[]
        self.name = basegraph.name
        assert isinstance(basegraph, CircuitGraph) ,"%s" % str(basegraph.__class__)
        
        # 调试的时候设置打印信息，调试完请改回False
        self.debug = False
        
        # 将所有的组合逻辑找到，相连接的归为一个Cloud
        self.__get_cloud_reg_graph(basegraph) 
        
        #只添加与PIPO-FD相连接的边，以及与Reg相连接的PIPO为cloud，
        #与组合逻辑相连接的PIPO，不影响CR图的拓扑结构，所以在函数中没有添加
        self.__add_pipo_empty_cloud() 

        # 在merge_cloud之前统计FD的扇出信息
        self.stat_fd_outdegree()

        # 将小的cloug 变为一个大的cloud函数里面，为图增加了 self.big_cloud的属性
        self.__merge_cloud()               
        if self.debug:
            print "------------info- After __merge_fd_cloud():------------------"
            self.info(True)
        # 确保构造出来的CloudRegGraph符合rules
        self.__check_rules()
        self.__check_rules2()

    def __get_cloud_reg_graph(self, basegraph):
        ''' 
            para: basegraph
            return: None
            add data attr -->> basegraph.cloud_reg_graph
            Model the circuit graph to a cloud(combinational cone)_register(FDs) graph
            注意：1.现有的cloud_register图中没有包含pipo节点，只是prim的节点
        '''
        # g2是一个用basegraph中的点和边建立的无向图，
        # 所以基本的节点和basegraph的节点是完全一致的，
        # 每一个节点都指向了m_list当中的原语的  cc.circuit_module() 对象的实例化
        print "Process: crgraph__get_cloud_reg_graph()...."
        g2=nx.Graph()
        g2.add_nodes_from(basegraph.prim_vertex_list)
        for eachEdge in basegraph.prim_edge_list:
            g2.add_edge(eachEdge[0][0],eachEdge[0][1])
        ## 方法2： 将原来的图中的所有节点和边都加到新的无向图中
        #g2=nx.Graph()
        #g2.add_nodes_from(basegraph.vertex_set)
        #for eachEdge in basegraph.edge_set:
        #    g2.add_edge(eachEdge[0][0],eachEdge[0][1])
        #------------------------------------------------------
        #step1 找出所有FD节点，并移去FD节点，以及VCC GND节点
        fd_list = []
        gnd_vcc = []
        for eachFD in basegraph.prim_vertex_list:
            if eachFD.m_type == 'FD' :
                fd_list.append(eachFD)
            elif eachFD.cellref in ['GND','VCC']:
                gnd_vcc.append(eachFD)
                print "Info: %s %s found" %(eachFD.cellref, eachFD.name)
        print "Info:%d fd has been found " % len(fd_list)
        g2.remove_nodes_from(fd_list)
        if gnd_vcc:
            g2.remove_nodes_from(gnd_vcc)
            print "Info: GND VCC node has been removed"
        #------------------------------------------------------
        #step2 找出连通分量,建立子图
        compon_list = []
        for c in nx.connected_components(g2):
            #连通子图            
            ccsub = g2.subgraph(c)
            compon_list.append(ccsub)
        print "Info: %d connected_componenent subgraph after remove FD [GND_VCC]*" % len(compon_list)

        #step2.1 
        #将每一个连通分量，也就是子图恢复为有向图，这样做的目的是搞清楚组合逻辑之间的连接关系
        #由于不存在组合逻辑回路，所以理论上，将全是组合的子图转换成有向图，边的数目完全相等
        #这可以通过下面的打印信息来查看
        #l2是compon_list的有向图版
        l2=[]
        cloud_num = 0
        for eachSubgraph in compon_list:
            h = nx.DiGraph(eachSubgraph)
            if eachSubgraph.number_of_nodes()>1:
                for eachEdge in h.edges():
                    if not basegraph.has_edge(eachEdge[0], eachEdge[1]):
                        h.remove_edge(eachEdge[0], eachEdge[1])
            l2.append(h)
            cloud_num += 1
            if self.debug == True: ##调试代码，只有打印的功能
                print "    ---- Cloud %d has %s prim :----" \
                    % (cloud_num ,eachSubgraph.number_of_nodes() )
                for eachPrim in eachSubgraph.nodes_iter():
                    eachPrim.__print__()
        #------------------------------------------------------
        #step3 记录下原图prim_edge_list中的 fd的D Q 端口与其他FD以及 与组合逻辑的有向边，以及节点
        special_edges=[]
        reg_reg_edges=[]
        fd_linked_nodes_edges={}
        for x in basegraph.prim_edge_list: 
            # x是每一个prim_prim_edge边 tuple, x=([prim1,prim2],[port1,port2],connection)
            for eachNode in x[0]:
               if eachNode.m_type == 'FD':
                  tmp= 1 if x[0].index(eachNode)==0 else 0
                  fd_port = x[1][1-tmp]  # 记录下来现在的FD的端口
                  other_prim = x[0][tmp] # 边的另一个prim
                  other_port = x[1][tmp] # 边的另一个port
                  if (other_prim.m_type != 'FD') and (fd_port.name in ['D','Q']):
                      non_fd_prim = other_prim
                      if not fd_linked_nodes_edges.has_key(non_fd_prim):
                          fd_linked_nodes_edges[non_fd_prim] = []
                      fd_linked_nodes_edges[non_fd_prim].append(x)
                  elif other_prim.m_type == 'FD' and (fd_port.name in ['D','Q'] ) and\
                      other_port.port_name in ['D','Q']:
                      reg_reg_edges.append(x)
                      break # 如果两个都是FD，那么建立连接之后，直接跳到下一条边
                            # 防止reg-reg edges重复建立
                  else:
                      # 特殊的边，包括其他原语的输出连接到D触发器的CE上
                      # 在CircuitGraph构造函数中，rules_check不检查CE信号，允许内部CE
                      # 但是这些信号对于构建CR图是没有作用的，所以这些边就不再加载到CR图中
                      if self.debug:
                        special_edge_info = (x[0][0].name,  x[1][0].name, x[0][1].name, x[1][1].name)
                        print "Info: special edge  %s %s %s %s" % special_edge_info
                      special_edges.append(x)

        #------------------------------------------------------
        #step4
        #新建一个有向图，节点为 cloud（step2获得的连通分量）+fd（step1获得）
        #              边为fd-cloud或者 fd-fd 的有向连接（step3获得）
        # vertex
        self.__add_clouds_from(l2)
        self.__add_regs_from(fd_list)
        # edge        
        for eachSubgraph in l2: # l2是cloud的list
            for eachNonFdPrim in fd_linked_nodes_edges.keys() : #cloud的边缘与FD相连接的NonFdPrim
                if eachSubgraph.has_node(eachNonFdPrim):
                    tmp_edge_list = fd_linked_nodes_edges[eachNonFdPrim]
                    for eachEdge in tmp_edge_list:
                        if eachEdge[0][0] == eachNonFdPrim:
                            ##注意，在这用等号是合法的，因为他们两都是原来的prim_vertex_set
                            ##在新添加边的时候，保留了在原图中的边的信息
                            self.add_edge(eachSubgraph, eachEdge[0][1], original_edge=eachEdge)
                        else:
                            assert eachEdge[0][1] == eachNonFdPrim
                            self.add_edge(eachEdge[0][0], eachSubgraph, original_edge=eachEdge)
        ##注意，在reg_reg_edges当中，边的元素，就是fd_list当中的module对象。所以这样做不会增加新的边
        for eachEdge in reg_reg_edges:
            # 在reg-reg 之间插入一个空的网络
            empty_cloud = nx.DiGraph()
            self.add_edge(eachEdge[0][0], empty_cloud, original_edge = eachEdge)
            self.add_edge(empty_cloud, eachEdge[0][1], original_edge = eachEdge)
            self.clouds.append(empty_cloud)
            cloud_num += 1
            if self.debug == True: 
                print "    ---- Cloud %d is empty cloud :----" % cloud_num
        if self.debug:
            print "------------Debug info- Before __merge_fd_cloud()-----------------:"
            print "     %d cloud, %d regs, %d edges" %\
                (len(self.clouds),len(self.regs),self.number_of_edges() )
        # ---------------------------------------------------------------------
        #basegraph添加新的cloud_reg_graph属性，也就是将两者绑定
        basegraph.cloud_reg_graph = self
        print "Note: get_cloud_reg_graph() succsfully"
        return None
    
    def __add_pipo_empty_cloud(self):
        '''在原图的pi_edge_list, po_edge_list,中寻找与FD的 [D,Q]端口相连接的边，
            如果找到，将该PI或者PO作为一个cloud加入到self中，将该边重新构建为cloud-reg边加入到图中
            如果该PIPO与别的组合逻辑PRIM相连接，或者与FD的非[D，Q]端口，比如CLR或者C连接，
            并不添加新的Cloud，一个PIPO多扇出的情况下，只将该PIPO连接到FD上。
        '''
        #TODO:处理一个PI扇出到多个FD的D端口的情况，应该添加几个Cloud？
        basegraph = self.basegraph
        include_pipo = basegraph.include_pipo
        regs = copy.copy(self.regs)
        if not include_pipo:
            print "Waring:Try to add_pipo empty cloud to self"
            raise CrgraphError
        pipo_egde = basegraph.pi_edge_list + basegraph.po_edge_list
        cnt = 0 #记录这个过程中添加了多少个PIPO-Reg 边
        pipo_2cloud = {}  # key:PIPO ,value: nx.Digraph,防止一个PIPO对应多个cloud
        while(regs):
            for edge in pipo_egde:
                if regs[-1] in edge[0]:
                    fd_index = edge[0].index(regs[-1])# FD_prim 在edge中的序号
                    fd_port = edge[1][fd_index]       # FD_port在edge[1]中记录
                    if not fd_port.port_name in ('D','Q'):
                        continue
                    pipo = edge[0][1-fd_index]        # 获取PIPO
                    cnt += 1
                    if not pipo_2cloud.has_key(pipo):     #如果还没有用过这个PIPO建立过图
                        pipo_cloud = nx.DiGraph()         #建立空图
                        pipo_cloud.add_node(pipo)         #添加PIPO节点
                        pipo_2cloud[pipo] = pipo_cloud    #更新 pipo->cloud字典
                        self.clouds.append(pipo_2cloud[pipo])    #将pipo对应的图加入到self.clouds[]属性中
                    if fd_index == 1:
                        self.add_edge(pipo_2cloud[pipo], regs[-1], original_edge = edge) #为crgraph添加边
                    else:
                        self.add_edge(regs[-1], pipo_2cloud[pipo], original_edge = edge) #为crgraph添加边
            #这个FD查找完了所有的PIPO边，将其从队列中移除，进行下一个FD的PIPO边查找
            regs.pop()
        print "Info: %d PIPO has been added to CloudRegGraph as cloud." % len(pipo_2cloud)
        print "Info: %d PIPO-Reg edge has been added to CloudRegGraph" % cnt
        print "Note: add_pipo_empty_cloud() to crgraph successfully ."

    def stat_fd_outdegree(self):
        '''统计在merge_cloud之前FD的fan-out频次，并将其打印到标准输出上
        '''
        out_degree = self.out_degree()
        fd_outdegree = { reg: out_degree[reg] for reg in self.regs}
        stat = {}
        for degree in fd_outdegree.values():
            if not stat.has_key(degree):
                stat[degree] = 1
            else:
                stat[degree] += 1
        print "FD's fanout stats are :"
        print "    fan-out    fd-number"
        for outdegree , frequency in stat.iteritems():
            print "    %d       %d" % (outdegree, frequency)
        return None
              
    def __merge_cloud(self):
        '合并多个cloud'
        # ------------------------------------------------------------------
        # step 1 对每一个多扇出的FD，将FD的多个扇出succ cloud合并成一个大的cloud
        print "Processing: merging cloud into big cloud "
        for eachFD in self.regs:
            if self.debug:
                print "    Processing %s ..." % eachFD.name
            # 不论有没有扇入只有0-1个扇出的时候，查找下一个FD
            # 有多于1个的扇出的时候，将它的后继节点的所有cloud合并为一个cloud
            # 合并的大cloud的前驱结点，也就是与同级FD相邻的FD与大cloud相连接
            # 合并的大cloud的所有后继结点，连接到大的cloud上面，进而完成的任务是
            # 每一个D只有一个扇出
            succs = self.successors(eachFD) #其中的每一个succ都是nx.DiGraph()
            if len(succs) <= 1:
                continue
            else: 
                big_cloud = nx.union_all( succs )
            pre_fds = set()
            succ_fds = set()
            for succ_cloud in self.successors(eachFD):
                pre_fds = pre_fds.union( set(self.predecessors(succ_cloud) ))
                succ_fds = succ_fds.union( set(self.successors(succ_cloud)) )
                self.remove_node(succ_cloud)
            self.add_node(big_cloud)
            if self.debug:
                print "        %d nodes in cuurent graph" % self.number_of_nodes()
                print "        %d egdes before adding edges-to bigclouds" % self.number_of_edges()
            for pre_fd in pre_fds:
                self.add_edge(pre_fd, big_cloud)
            for succ_fd in succ_fds:
                #self.add_edge(big_cloud, pre_fd) ######FUCK THIS BUGGGG
                self.add_edge(big_cloud, succ_fd)
            if self.debug:
                print "        %d edges in current graph" % self.number_of_edges()
        # ------------------------------------------------------------------
        # step2 合并每一个FD的所有后继Cloud节点，把他们组成大的Big_Cloud
        self.big_clouds = []
        for node in self.nodes_iter(): #总终图上的nx.DiGraph类型只能是cloud
            if isinstance(node , nx.DiGraph):
                cloud = node   
                self.big_clouds.append( cloud )
        print "Note: merge_cloud() successfully."
        return None

    def __add_clouds_from(self, list1):
        '''输入list1,判断list1当中的所有每一个元素的类型，之后nx.DiGraph类型才能
            成为cloud
        '''
        for eachCloud in list1:
            assert isinstance(eachCloud, nx.DiGraph)
            self.clouds.append(eachCloud)
            self.add_node(eachCloud)

    def __add_regs_from(self, list1):
        '''输入list1,判断list1当中的每一个元素的类型，只有cc.circuitmodule类型
        并且m_type == "FD"的元素才能成为reg
        '''
        for eachFD in list1:
            assert isinstance(eachFD, cc.circut_module) and\
                eachFD.m_type == 'FD', eachFD.name
            self.add_node(eachFD)
            self.regs.append(eachFD)
 
    def __check_rules(self):
        ''' 确保每一个D触发器只有一个扇入，一个扇出
        '''
        for reg in self.regs:
            npre = len(self.predecessors(reg))
            nsuc = len(self.successors(reg))
            if  npre > 1:
                print "Crgrpah Rules Error : %s %s has %d >1 predecessors" %\
                    (reg.cellref, reg.name, npre)
                print "\n".join([ str(eachPre.__class__) for eachPre in self.predecessors(reg)])
                raise CrgraphRuleError
            if  nsuc != 1:
                print "Crgrpah Rules Error : %s %s has  %d successors" %\
                    (reg.cellref, reg.name, nsuc)
                print "\n".join([ str(eachSuc.__class__) for eachSuc in self.successors(reg)])
                raise CrgraphRuleError
        print "Info:Check Rules of cloud_reg_graph succfully,\n    none of FD has more than 2 degree"

    def __check_rules2(self):
        "确保图中的每一条边都是FD-Cloud边，也就是每一条边含有两种元素,"
        for edge in self.edges_iter():
            has_fd = False
            has_cloud = False
            for i in range(2):
                if isinstance(edge[i], cc.circut_module) :
                    if has_fd:
                        print "Error: Crgraph ChcekRules2 Error ,Non FD-Cloud edge found, its FD-FD Edge %s" %(str (edge))
                        raise CrgraphRuleError
                    has_fd =True
                    fd = edge[i]
                if isinstance(edge[i], nx.DiGraph) and edge[i] in self.big_clouds:
                    if has_cloud:
                        print 'Error: Crgraph CheckRules2 Error ,Non FD-Cloud edge found, its Cloud-Cloud Edge %s' % ( str(edge) )
                        raise CrgraphRuleError
                    has_cloud = True
                    cloud = edge[i]
            if not (has_fd and has_cloud): #没有FD或者没有Cloud，根据前面的情况，肯定有一个cloud或者一个fd存在
                print "Error: Crgraph CheckRules2 Error, egde %s\n    has %d Cloud %d FD" \
                            % ( str(edge),int(has_cloud),int(has_fd) )
                raise CrgraphRuleError
        print "Info: Check Rules2 of cloud_reg_graph succfully,\n    every edge is FD-cloud edge"

    def paint(self):
        label_dict={}
        for eachCloud in self.big_clouds:
            if eachCloud.number_of_nodes()>1:
                label_dict[eachCloud] = 'cloud'
            elif eachCloud.number_of_nodes() == 1:
                node = eachCloud.nodes()[0]
                if isinstance(node, cc.circut_module):
                    label_dict[eachCloud] = "cloud:"+ node.cellref + ":" + node.name
                else: #its a port node
                    label_dict[eachCloud] = node.port_type +":"+node.port_name
            else:
                label_dict[eachCloud] = 'empty_cloud'
        for eachReg in self.regs:
            label_dict[eachReg] = eachReg.cellref + ":" + eachReg.name
        ps= nx.random_layout(self)
        import matplotlib.pylab as plt
        nx.draw_networkx_nodes(self, pos=ps, nodelist = self.big_clouds, node_color = 'r')
        nx.draw_networkx_nodes(self, pos=ps, nodelist = self.regs, node_color = 'g')
        nx.draw_networkx_edges(self,ps)
        nx.draw_networkx_labels(self,ps,labels=label_dict)
        plt.show()
        return True

    def crlayout(self,default = True):
        '''设置CloudRegGraph图的节点位置
        '''
        fds = self.regs
        clouds = self.clouds
        ps = {} #存储每一个节点的位置的字典
        if default:
            ps = nx.random_layout(self)
            return ps
        # TODO: compute each node's position
        return ps

    def info(self , verbose = False):
        print "--------------Cloud_Reg_graph info:-----------------"
        print nx.info(self)
        ncloud = 0
        nreg = 0
        for node in self.nodes_iter():
            if isinstance(node, nx.DiGraph): 
                ncloud += 1
                if node.number_of_nodes() == 0:
                    if verbose: print "cloud ::\n empty cloud\n"
                    continue
                if verbose: print "cloud ::"
                for prim in node.nodes_iter():
                    assert isinstance(prim, (cc.circut_module, cc.port)),\
                         "cloud type %s " % str(prim.__class__)              
                    if verbose: prim.__print__()
            else:
                assert isinstance(node ,cc.circut_module) ,"reg type %s " % str(node.__class__)
                if verbose:
                    print "fd ::"                
                    node.__print__()                
                nreg += 1
        assert  len(self.big_clouds) == ncloud ,"%d %d"%(len(self.big_clouds),ncloud)
        print "Number of cloud:%d " % ncloud
        print "Number of register:%d" % nreg
        print "--------------------------------------"

    def to_gexf_file(self, filename):
        '''输出图的信息到指定的gexf文件中'''
        new_graph =nx.DiGraph()
        fobj = open(self.name+"fdnameid.gexf",'w')
        for reg in self.regs:
            fobj.write(reg.name+"\n")
            reg_id = '_d_'+reg.name[1:] if reg.name[0]=='\\' else reg.name
            new_graph.add_node(reg, id =reg_id, label = reg.cellref)
        fobj.close()
        for cloud in self.big_clouds:
            new_graph.add_node(cloud, id= id(cloud),label= 'cloud')
        for eachEdge in self.edges_iter():
            new_graph.add_edge(eachEdge[0],eachEdge[1])
        nx.write_gexf(new_graph, filename)
#------------------------------------------------------------------------------
# 模块测试代码
#------------------------------------------------------------------------------
def __test():
    '''crgraph本模块的测试
    '''
    from circuitgraph import get_graph_from_raw_input
    g2 = get_graph_from_raw_input() # 输入netlist 文件，得到 CircuitGraph对象g2
    g2.info() #打印原图的详细信息
    cr2 = CloudRegGraph(g2) 
    cr2.info()
    cr2.to_gexf_file("tmp\\%s_crgraph.gexf" % cr2.name)
    if cr2.number_of_nodes() <= 100:
        plt.figure( cr2.name+"_crgraph")
        cr2.paint()
if __name__ == '__main__':
    import matplotlib.pylab as plt
    __test()

    
    