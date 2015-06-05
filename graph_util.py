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
    
    #clock_set=[]
    #edge_set=[]
    edge_set2=[]   
    PI_edge=[]
    PO_edge=[]
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

    linkable_port=['D','Q','CE']
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
#                        if eachPort.port_type!='output':
#                            print "Warning: None-output  port connecnt to PO. module:"\
#                                +eachModule.name+" port ."+eachPort.port_name+'('+eachPort.port_assign+")"
                        PO_edge.append([eachModule.name,eachPPort])
    
    #----------ALL other Module edge
    i=1
    print "Process: constructing m-m edges..."
    for eachModule in m_list[1:]:
#        if verbose:        
#            print "Process: node %d edges for %s" % (i,eachModule.name),
        for eachPort in eachModule.port_list:
#            if eachPort.port_type=='clock' and (eachPort.port_assign not in clock_set):
#                clock_set.append(eachPort.port_assign)
#                continue
            if (eachModule.m_type=='FD') and (eachPort.port_name in linkable_port):
                continue
            else:
                for eachModule2 in m_list[1:]:
                    for eachPort2 in eachModule2.port_list:
                        if eachPort2.port_type==eachPort.port_type:
                            continue
                        elif (eachModule.m_type=='FD') and (eachPort.port_name in linkable_port):
                            continue
                        elif eachPort2.port_assign==eachPort.port_assign:
                            if (eachPort.port_type=='input' and eachPort2.port_type=='output'):
                                #if [m_list.index(eachModule2),m_list.index(eachModule)] not in edge_set:
                                s_node=eachModule2.name
                                d_node=eachModule.name
                                #edge_set2.append([eachModule2.name,eachModule.name])
                                #edge_set.append([m_list.index(eachModule2),m_list.index(eachModule)])
                            elif (eachPort.port_type=='output' and eachPort2.port_type=='input'):
                                #if [m_list.index(eachModule),m_list.index(eachModule2)] not in edge_set:
                                #edge_set2.append([eachModule.name,eachModule2.name])
                                s_node=eachModule.name
                                d_node=eachModule2.name
                                #edge_set.append([m_list.index(eachModule),m_list.index(eachModule2)])
                            if [s_node,d_node] not in edge_set2:
                                edge_set2.append([s_node,d_node])
                        elif (eachModule==eachModule2 and eachPort==eachPort2):
                            continue
#        if(verbose):
#            print "done !"
        i=i+1
    print "Process: searching every module for edges done !"
    #--------merge all the edge 
    edge_set2=edge_set2+PI_edge+PO_edge 
    graph=nx.DiGraph()
    graph.add_edges_from(edge_set2)
    #--------print info part 
    if verbose:
        print 'Info:vertex number is: %d'% len(vertex_set)
        print 'Info:vertex_set ARE:-----------------------------------------------'
        for eachVertex in vertex_set:
            print  vertex_set_dict[eachVertex]+'::::'+eachVertex
        print 'Info:edge   number is: %d'% len(edge_set2)        
        print 'Info:edge_set   ARE:-----------------------------------------------'
        for eachEdge in edge_set2:
            print vertex_set_dict[eachEdge[0]]\
                    +"-->>"+vertex_set_dict[eachEdge[1]]+"::::"+str(eachEdge)
#        print 'Info:clock_set  ARE:-----------------------------------------------'
#        for eachClock in clock_set:
#            print eachClock   
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
    ## travrse all the nodes and deal with non-FD PI PO nodes 
    i=1
    for eachVertex in vertex_set_tmp:
        #update all the edge set when finishes iterate a node         
        edge_set_tmp  =copy.deepcopy(edge_set_cpy)  
        if  vertex_set_dict[eachVertex] not in ['FD','PI','PO']:
#            if (verbose):
#                print "Process:%d node %s %s being erased..." \
#                        %(i,vertex_set_dict[eachVertex],eachVertex),
            ##把一个所有非FD PI PO的点的所有出与入相连接
            s_node=[]
            d_node=[]
            for eachEdge in edge_set_tmp:
                if eachVertex not in eachEdge:
                    continue
                elif eachVertex==eachEdge[0]:
                    d_node.append(eachEdge[1])
                    safe_remove(edge_set_cpy,eachEdge)
                elif eachVertex==eachEdge[1]:
                    s_node.append(eachEdge[0])
                    safe_remove(edge_set_cpy,eachEdge)
#                    for eachEdge2 in edge_set_tmp:
#                        if eachVertex==eachEdge2[1]:
#                            s_node=eachEdge2[0]
#                            safe_remove(edge_set_cpy,eachEdge2)
            if len(s_node)!=0 and len(d_node)!=0:
                for eachSnode in s_node:
                    for eachDnode in d_node:
                        if [eachSnode,eachDnode] not in edge_set_cpy:
                            edge_set_cpy.append([eachSnode,eachDnode])
            vertex_set_cpy.remove(eachVertex)
#            if (verbose):
#                print "done! NEW:%d * %d" %(len(s_node),len(d_node))
            i=i+1
    ##asseert that check every edge in s_graph is FD PI PO-->>FD PI PO edge
    for eachEdge in edge_set_cpy:
        for eachNode in eachEdge:
            assert eachNode in vertex_set_cpy,"Error: none FD edge found!!" +str(eachEdge)+\
                vertex_set_dict[eachEdge[0]]+"-->>"+vertex_set_dict[eachEdge[1]]          
    
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
        print s_graph.nodes_with_selfloops()
    print "Note: construct_s_graph() successfully!"
    return s_graph,edge_set_cpy,vertex_set_cpy
     
###############################################################################
def visualize_s_graph(vertex_set,vertex_set_dict,edge_set2,fname):    
    graph=nx.DiGraph()  
    pi_vertex=[]
    po_vertex=[]
    fd_vertex=[]    
    for eachVertex in vertex_set:
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
    graph.add_edges_from(edge_set2)

    ps=nx.spring_layout(graph)
    nx.draw_networkx_nodes(graph,pos=ps,nodelist=pi_vertex,node_color='r')
    nx.draw_networkx_nodes(graph,pos=ps,nodelist=po_vertex,node_color='b')
    nx.draw_networkx_nodes(graph,pos=ps,nodelist=fd_vertex,node_color='g')
    nx.draw_networkx_edges(graph,ps)
    nx.draw_networkx_labels(graph,ps)
    plt.savefig(fname+".png")   
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
#   visualize_s_graph(s_vertex,vertex_set_dict,s_edge,fname)
#   logic_depth_dict=calc_logic_depth(s_graph,vertex_set_dict)    
    ###setup output file dir
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
    
    
    