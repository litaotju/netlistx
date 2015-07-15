# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 13:35:57 2015

@author: litao
"""
import networkx as nx
import matplotlib.pyplot as plt
import copy
import os.path

import class_circuit as cc
###############################################################################
class s_graph(nx.DiGraph):
    def __init__(self,name,edge_set,vertex_set,include_pipo=True,verbose=False): 
        nx.DiGraph.__init__(self)
        self.include_pipo=include_pipo
        ##设置保留下来的节点类型,如果m_type在该list中,就不进行ignore
        self.care_vertex_type=('FD')
        ##因为只需要对新的列表的元素进行操作,而不需要关心元素的内容到底是什么
        ##所以只需要进行copy.copy而不需要进行更深程度的复制
        vertex_set_cpy =copy.copy(vertex_set)
        vertex_set_tmp =copy.copy(vertex_set_cpy)
        edge_set_cpy   =copy.copy(edge_set)
        i=1 
        print "Process: erasing not cared nodes of the circuit"
        #######################################################################
        # travrse all the nodes and deal with non-FD PI PO nodes 
        for eachVertex in vertex_set_tmp:
            #update all the edge set when finishes iterate a node
            #使用上一次的迭代结果,更新了边集,进行下一次的迭代
            edge_set_tmp  =copy.copy(edge_set_cpy)  
            if  (isinstance(eachVertex,cc.circut_module) \
                    and eachVertex.m_type not in self.care_vertex_type):
                if (verbose):
                    print "Process:%d node %s %s being erased..." \
                            %(i,eachVertex.m_type,eachVertex.name),            
                s_node=[]
                d_node=[]
                ##把一个所有非FD PI PO的点的所有出与入相连接
                for eachEdge in edge_set_tmp:
                    if eachVertex not in eachEdge[0]:
                        continue
                    elif eachVertex==eachEdge[0][0]:
                        d_node.append([eachEdge[0][1],eachEdge[1][1]])                        
                        edge_set_cpy.remove(eachEdge)
                    elif eachVertex==eachEdge[0][1]:
                        s_node.append([eachEdge[0][0],eachEdge[1][0]])
                        edge_set_cpy.remove(eachEdge)
                #如果当前节点既有前驱也有后继，将他们排列组合相连接，然后加入边集
                if len(s_node)!=0 and len(d_node)!=0:
                    for eachSnode in s_node:
                        for eachDnode in d_node:
                            edge_set_cpy.append([[eachSnode[0],eachDnode[0]],[eachSnode[1],eachDnode[1]]])
                vertex_set_cpy.remove(eachVertex)
                if (verbose):
                    print "done!"
                i=i+1
        ###########################################################################
        self.name =name
        self.fd_nodes=[]
        self.pi_nodes=[]
        self.po_nodes=[]
        for eachVertex in vertex_set_cpy:
            if isinstance(eachVertex,cc.circut_module) and (eachVertex.m_type in self.care_vertex_type):
                self.fd_nodes.append(eachVertex)
                node_type=eachVertex.cellref
            elif isinstance(eachVertex,cc.port) and eachVertex.port_type=='input':
                self.pi_nodes.append(eachVertex)
                node_type=eachVertex.port_type
            else:
                assert (isinstance(eachVertex,cc.port) and eachVertex.port_type=='output'),\
                    "vertex type:%s" % (eachVertex.__class__())
                node_type=eachVertex.port_type
                self.po_nodes.append(eachVertex)
            self.add_node(eachVertex,node_type=node_type,name=eachVertex.name)
        for eachEdge in edge_set_cpy:
            self.add_edge(eachEdge[0][0],eachEdge[0][1],\
                            port_pair=[eachEdge[1][0],eachEdge[1][1]])
        self.fd_depth_dict={}
        if self.include_pipo:
            self.compu_fds_depth(verbose)
    ###############################################################################
    def paint(self,display_pipo=True,order=False):
        'no mamupulation of nodes or edges in this func, just pict graph'
        if order:
            #------------------------------------
            #需要改进
            #获取最大的逻辑深度,以及X坐标方向的长度
            max_depth=0
            for eachFD in self.fd_nodes:
                if self.fd_depth_dict[eachFD][1]:
                    tmp2=self.fd_depth_dict[eachFD][0]
                    if tmp2>max_depth:
                        max_depth=tmp2
                else:
                    continue
            pos_dict={}
            x_max=2+max_depth   
            #计算每一个点的横纵坐标，横坐标为逻辑深度，纵坐标为在本一行当中的排序
            cnt=[]
            for i in range(0,max_depth+1):
                cnt.append(0)
            cnt[0]=len(self.pi_nodes)
            cnt[-1]=len(self.po_nodes)
            
            for eachPi in self.pi_nodes:
                pos_dict[eachPi]=(0,self.pi_nodes.index(eachPi))
            for eachPo in self.po_nodes:
                pos_dict[eachPo]=(max_depth+1,self.po_nodes.index(eachPo)) 
            for i in range(1,max_depth+1):
                for eachFD in self.fd_nodes:
                    if self.fd_depth_dict[eachFD][1]==True:
                        if self.fd_depth_dict[eachFD][0]==i:
                            cnt[i]=cnt[i]+1
                            pos_dict[eachFD]=(self.fd_depth_dict[eachFD][0],cnt[i])
                    else:
                        pos_dict[eachFD]=(x_max,0)
                 
            y_max=max(cnt)   
            ps=pos_dict
        else:
            ps=nx.spring_layout(self)
        #--------------------------------
        #根据前面算出来的位置信息进行节点与边的绘制
        #-------------------------------
        if display_pipo:        
            nx.draw_networkx_nodes(self,pos=ps,nodelist=self.pi_nodes,node_color='r')
            nx.draw_networkx_nodes(self,pos=ps,nodelist=self.po_nodes,node_color='b')
        nx.draw_networkx_nodes(self,pos=ps,nodelist=self.fd_nodes,node_color='g')
        nx.draw_networkx_edges(self,ps)
        label_dict={}
        label_pos={}
        if display_pipo:
            for eachVertex in self.pi_nodes+self.po_nodes:
                label_dict[eachVertex]=eachVertex.port_type+"\n"+eachVertex.port_name
                label_pos[eachVertex]=(pos_dict[eachVertex][0]+0.2,pos_dict[eachVertex][1])
        for eachVertex in self.fd_nodes:
            label_dict[eachVertex]=eachVertex.cellref+"\n"+eachVertex.name
            if order:
                label_pos[eachVertex]=(pos_dict[eachVertex][0]+0.2,pos_dict[eachVertex][1])
        self.label_dict=label_dict
        if order:
            nx.draw_networkx_labels(self,pos=label_pos,labels=label_dict,font_color='m')
        else:
            nx.draw_networkx_labels(self,pos=ps,labels=label_dict,font_color='m')
        ##---------------------------------------------------------------------
        ##保存绘图到当前路径下的 tmp/文件夹
        pic_dir=os.getcwd()+"//tmp//"
        pic_full_name=pic_dir+self.name+"_s_graph.png"
        plt.savefig(pic_full_name) 
        
    ###########################################################################
    def info(self):
        print 'Info: s_vertex:---------------------------------------------'
        for eachVertex in self.nodes_iter():
            if isinstance(eachVertex,cc.circut_module):
                print eachVertex.m_type+':'+eachVertex.name
            else:
                print eachVertex.port_type+':'+eachVertex.port_name
        print 'Info: s_edge  :--------------------------------------------'
        for eachEdge in self.edges_iter():
            print "%s --->>%s "%(eachEdge[0].name,eachEdge[1].name)
        print "S_graph info:nx.info(self)---------------------------------"             
        print nx.info(self)
        print "Info: nodes with selfloops ARE:----------------------------"
        for eachNode in self.nodes_with_selfloops():
            print eachNode
    ###########################################################################        
    def compu_fds_depth(self,verbose):
        for eachFD in self.fd_nodes:
            has_cnt2_pi=False
            tmp_depth=1000000
            tmp_path=(None,None)
            for eachPi in self.pi_nodes :
                if not (eachPi.port_name=='clk' or eachPi.port_name=='reset'):
                    if nx.has_path(self,source=eachPi, target=eachFD):
                        has_cnt2_pi=True
                        tmp_depth2=nx.shortest_path_length(self,source=eachPi,target=eachFD)
                        if tmp_depth2<tmp_depth:
                            tmp_depth=tmp_depth2
                            tmp_path =(eachPi,eachFD)
                        else:
                            continue
            self.fd_depth_dict[eachFD]=(tmp_depth,has_cnt2_pi,tmp_path)
            if (verbose):
                print "Node:%s %s .depth is: %d. path is :" \
                    %(eachFD.cellref,eachFD.name,tmp_depth)
                      