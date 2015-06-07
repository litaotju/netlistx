# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
"""
import networkx as nx
import matplotlib.pyplot as plt
import netlist_util as nu
import copy
import os.path
###############################################################################
def get_edge_vertex(m_list,verbose=False):
    '---this func is to construct a s-graph of a circut---'
    vertex_set_dict={}
    vertex_set=[]
    PI_vertex=[]
    PO_vertex=[]
    edge_set2=[]   
    PI_edge=[]
    PO_edge=[]
    ###########################################################################
    #vertex
    # ---------- PI　vertex
    for eachPPort in m_list[0].port_list:
        if eachPPort.port_type=='input':
            if eachPPort.port_width>1:           
                for i in range(0,eachPPort.port_width):
                    PI_vertex.append(eachPPort.port_name+'['+str(i)+']')
                    vertex_set.append(eachPPort.port_name+'['+str(i)+']')
                    vertex_set_dict[eachPPort.port_name+'['+str(i)+']']="P"+eachPPort.port_type[0].upper()
            else:
                vertex_set_dict[eachPPort.port_name]="P"+eachPPort.port_type[0].upper()
                vertex_set.append(eachPPort.port_name)
                PI_vertex.append(eachPPort.port_name)
    #------------module vertex
    for eachModule in m_list[1:]:
        vertex_set_dict[eachModule.name]=eachModule.m_type
        vertex_set.append(eachModule.name)
    #------------PO vertex
    for eachPPort in m_list[0].port_list:
        if eachPPort.port_type=='output':
            if eachPPort.port_width>1:           
                for i in range(0,eachPPort.port_width):
                    PO_vertex.append(eachPPort.port_name+'['+str(i)+']')
                    vertex_set.append(eachPPort.port_name+'['+str(i)+']')
                    vertex_set_dict[eachPPort.port_name+'['+str(i)+']']="P"+eachPPort.port_type[0].upper()
            else:
                vertex_set_dict[eachPPort.port_name]="P"+eachPPort.port_type[0].upper()
                vertex_set.append(eachPPort.port_name)
                PO_vertex.append(eachPPort.port_name)


    ###########################################################################
    #edge
    linkable_port=('D','Q','CE')
    #-----------PI PO edge excluding clock and  reset
    print "Process: searching PI and PO edges..."
    for eachModule in m_list[1:]:
        for eachPort in eachModule.port_list:
            if (eachModule.m_type=='FD') and (eachPort.port_name not in linkable_port):
                continue
            else:
                for eachPPort in PI_vertex:
                    if eachPort.port_assign==eachPPort:
                        assert eachPort.port_type=='input',"None-input port connect to PI. module:"\
                        +eachModule.name+" port:"+eachPort.port_name+'('+eachPort.port_assign+") "\
                        +eachPort.port_type
                        PI_edge.append([eachPPort,eachModule.name])
                for eachPPort in PO_vertex:
                    if eachPort.port_assign==eachPPort:
                        if eachPort.port_type=='input':
#                        if eachPort.port_type!='output':
#                            print "Warning: None-output  port connecnt to PO. module:"\
#                                +eachModule.name+" port ."+eachPort.port_name+'('+eachPort.port_assign+")"
                            PO_edge.append([eachPPort,eachModule.name])
                        else:
                            PO_edge.append([eachModule.name,eachPPort])
    
    #----------ALL other Module edge
    i=1
    print "Process: constructing m-m edges..."
    for eachModule in m_list[1:]:
        if verbose:        
            print "Process: node %d edges for %s" % (i,eachModule.name),
        for eachPort in eachModule.port_list:
            if (eachModule.m_type=='FD') and (eachPort.port_name not in linkable_port):
                continue
            else:
                for eachModule2 in m_list[1:]:
                    for eachPort2 in eachModule2.port_list:
                        if eachPort2.port_type==eachPort.port_type:
                            continue
                        elif (eachModule.m_type=='FD') and (eachPort.port_name not in linkable_port):
                            continue
                        elif eachPort2.port_assign==eachPort.port_assign:
                            if (eachPort.port_type=='input' and eachPort2.port_type=='output'):
                                s_node=eachModule2.name
                                d_node=eachModule.name
                            elif (eachPort.port_type=='output' and eachPort2.port_type=='input'):
                                s_node=eachModule.name
                                d_node=eachModule2.name
                            if [s_node,d_node] not in edge_set2:
                                edge_set2.append([s_node,d_node])
        if(verbose):
            print "done !"
        i=i+1
    print "Process: searching every module for edges done !"
    #--------merge all the edge 
    edge_set2=edge_set2+PI_edge+PO_edge 
    
    ###########################################################################
    #--------new a networkx graph object    
    graph=nx.DiGraph()
    graph.add_edges_from(edge_set2)
    #--------print info part 
    if verbose:
        print 'Info:vertex number is: %d'% len(vertex_set)
        print 'Info:vertex_set ARE:--------------------------------------------'
        for eachVertex in vertex_set:
            print  vertex_set_dict[eachVertex]+'::::'+eachVertex
        print 'Info:edge   number is: %d'% len(edge_set2)        
        print 'Info:edge_set   ARE:--------------------------------------------'
        for eachEdge in edge_set2:
            print vertex_set_dict[eachEdge[0]]\
                    +"-->>"+vertex_set_dict[eachEdge[1]]+"::::"+str(eachEdge)
    print 'Note: get_edge_vertex() successfully !'
    return graph,vertex_set,vertex_set_dict,edge_set2 #,PI_edge,PO_edge 

###############################################################################
def safe_remove(sequence,element):
    if element in sequence:
        sequence.remove(element)
    else:
        pass
    return True
###############################################################################
#def construct_s_graph_new(graph,vertex_set_dict,verbose=False):
#    s_graph=graph.copy()
#    for eachNode in nx.nodes_iter(graph):
#        source_set=[]
#        destiny_set=[]
#        new_edge=[]
#        if vertex_set_dict[eachNode] not in ['FD','PI','PO']:
#            source_set =nx.dfs_predecessors(graph,eachNode)
#            print "Node:%s " % eachNode
#            print "predecessor is: %s" % str(source_set)
#            destiny_set=nx.dfs_successors(graph,eachNode)
#            s_graph.remove_node(eachNode)
#            print eachNode+vertex_set_dict[eachNode]
#            for eachSource in source_set:
#                for eachDes in destiny_set:
#                    new_edge.append([eachSource,eachDes])
#                    print [eachSource,eachDes]
#            s_graph.add_edges_from(new_edge)
#    if verbose:
#        print "S_graph info:----------------------------------------------"             
#        print nx.info(s_graph)
#        print "Info: nodes with selfloops ARE:----------------------------"
#        print s_graph.nodes_with_selfloops()
#    print "Func: construct_s_graph_new() successfully !"
#    return s_graph

    
###############################################################################   
def construct_s_graph(edge_set2,vertex_set,vertex_set_dict,verbose=False):
    print "Func-call: into construct_s_graph() "
 
    edge_set_cpy   =copy.deepcopy(edge_set2)
    vertex_set_cpy =copy.deepcopy(vertex_set)
    vertex_set_tmp =copy.deepcopy(vertex_set_cpy)  
    i=1
    care_vertex_type=('FD','PI','PO')
    ###########################################################################
    # travrse all the nodes and deal with non-FD PI PO nodes 
    for eachVertex in vertex_set_tmp:
        #update all the edge set when finishes iterate a node         
        edge_set_tmp  =copy.deepcopy(edge_set_cpy)  
        if  vertex_set_dict[eachVertex] not in care_vertex_type:
            if (verbose):
                print "Process:%d node %s %s being erased..." \
                        %(i,vertex_set_dict[eachVertex],eachVertex),            
            s_node=[]
            d_node=[]
            ##把一个所有非FD PI PO的点的所有出与入相连接
            for eachEdge in edge_set_tmp:
                if eachVertex not in eachEdge:
                    continue
                elif eachVertex==eachEdge[0]:
                    d_node.append(eachEdge[1])
                    edge_set_cpy.remove(eachEdge)
                    #safe_remove(edge_set_cpy,eachEdge)
                elif eachVertex==eachEdge[1]:
                    s_node.append(eachEdge[0])
                    edge_set_cpy.remove(eachEdge)
                    #safe_remove(edge_set_cpy,eachEdge)
            #如果当前节点既有前驱也有后继，将他们排列组合相连接，然后加入边集
            if len(s_node)!=0 and len(d_node)!=0:
                for eachSnode in s_node:
                    for eachDnode in d_node:
                        if [eachSnode,eachDnode] not in edge_set_cpy:
                            edge_set_cpy.append([eachSnode,eachDnode])
            vertex_set_cpy.remove(eachVertex)
            if (verbose):
                print "done!"
            i=i+1
    ###########################################################################

    #asseert that check every edge in s_graph is FD PI PO-->>FD PI PO edge
#    print "Process: checking the every node in s_graph..."
#    for eachEdge in edge_set_cpy:
#        for eachNode in eachEdge:
#            assert eachNode in vertex_set_cpy,"Error: none-FD node found!!" \
#            +str(eachEdge)+vertex_set_dict[eachEdge[0]]+"-->>"+vertex_set_dict[eachEdge[1]]          
#    print "Process: successfully, every node is in [FD,PI,PO] type."
    
    #instance a networkx graph class object
    s_graph=nx.DiGraph()        
    s_graph.add_edges_from(edge_set_cpy)   

    if (verbose):
        print 'Info: s_vertex:-----------------------------------------------------'
        for eachVertex in vertex_set_cpy:
            print vertex_set_dict[eachVertex]+'::::'+eachVertex
        print 'Info: s_edge  :-----------------------------------------------------'
        for eachEdge in edge_set_cpy:
            print "["+vertex_set_dict[eachEdge[0]]\
            +"-->>"+vertex_set_dict[eachEdge[1]]+"]::::" +str(eachEdge)
        print "S_graph info:----------------------------------------------"             
        print nx.info(s_graph)
        print "Info: nodes with selfloops ARE:----------------------------"
        for eachNode in s_graph.nodes_with_selfloops():
            print eachNode
    print "Note: construct_s_graph() successfully!"
    return s_graph,edge_set_cpy,vertex_set_cpy
     
###############################################################################
def visualize_s_graph(s_vertex_set,vertex_set_dict,s_edge_set,fname,display_pipo=True):    
    graph=nx.DiGraph() 
    #节点的分类，以便于进行染色
    pi_vertex=[]
    po_vertex=[]
    fd_vertex=[]    
    for eachVertex in s_vertex_set:
        if vertex_set_dict[eachVertex]=='PI':
            pi_vertex.append(eachVertex)
        elif vertex_set_dict[eachVertex]=='PO':
            po_vertex.append(eachVertex)
        else:
            assert vertex_set_dict[eachVertex]=='FD',\
            "None PI or PO or FD nodes in s_graph"
            fd_vertex.append(eachVertex)
    graph.add_nodes_from(pi_vertex)
    graph.add_nodes_from(po_vertex)
    graph.add_nodes_from(fd_vertex)     
    graph.add_edges_from(s_edge_set)
    #设置layout
    ps=nx.spring_layout(graph)
    
    if display_pipo==False:        
        graph.remove_nodes_from(pi_vertex+po_vertex)
    else:
        nx.draw_networkx_nodes(graph,pos=ps,nodelist=pi_vertex,node_color='r')
        nx.draw_networkx_nodes(graph,pos=ps,nodelist=po_vertex,node_color='b')
    nx.draw_networkx_nodes(graph,pos=ps,nodelist=fd_vertex,node_color='g')
    nx.draw_networkx_edges(graph,ps)
    nx.draw_networkx_labels(graph,ps)
    
    pic_dir=os.getcwd()+"//tmp//"
    name_base=os.path.splitext(fname)
    pic_full_name=pic_dir+name_base[0]+".png"
    plt.savefig(pic_full_name)   
    return True

###############################################################################
def calc_logic_depth(s_graph,vertex_set_dict):
    pi_set=[]    
    for eachVertex in vertex_set_dict.keys():
        if vertex_set_dict[eachVertex]=='PI':
            pi_set.append(eachVertex)
    logic_depth_dict={}
    for eachNode in nx.nodes_iter(s_graph):
        if vertex_set_dict[eachNode]=='FD':
            tmp=[]
            for eachPi in pi_set :
                if eachPi in nx.nodes_iter(s_graph):             
                    depth=nx.shortest_path_length(s_graph,source=eachPi,target=eachNode)
                    tmp.append(depth)
            logic_depth=min(depth for depth in tmp)
            logic_depth_dict[eachNode]=logic_depth
            print "Node:"+eachNode+".depth: "+str(logic_depth)        
    return logic_depth_dict
    
###############################################################################
if __name__=="__main__":
    fname=raw_input("plz enter filename:")
    signal_list,m_list,defparam_init_list       = nu.extract_m_list(fname,verbose=False)
    graph,vertex_set,vertex_set_dict,edge_set2  = get_edge_vertex(m_list,verbose=True)
    s_graph,s_edge,s_vertex                     = construct_s_graph(edge_set2,vertex_set,\
                                                    vertex_set_dict,verbose=True)   
#   s_graph=construct_s_graph_new(graph,vertex_set_dict,verbose=True)
    visualize_s_graph(s_vertex,vertex_set_dict,s_edge,fname,display_pipo=False)
#   logic_depth_dict=calc_logic_depth(s_graph,vertex_set_dict)    
    
    #########################################################################                                                
    ###setup output file dir输出设置
    name_base=os.path.splitext(fname)
    output_dir=os.getcwd()+"//test_output_dir//vertex_edge//"   
    fobj=open(output_dir+name_base[0]+'_eg.txt','w')
    fobj2=open(output_dir+name_base[0]+'_vet.txt','w')
    for eachEdge in s_edge:
        fobj.writelines(str(eachEdge[0])+' '+str(eachEdge[1])+'\n')
    for eachVertex in s_vertex:
       fobj2.writelines(eachVertex+':::::'+vertex_set_dict[eachVertex]+'\n')
    fobj.close()
    fobj2.close()
    
    
    