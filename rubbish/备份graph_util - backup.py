# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
"""
import re
import networkx as nx
import matplotlib.pyplot as plt
import netlist_util as nu
import copy
###############################################################################
def get_edge_vertex(m_list,verbose=True):
    '---this func is to construct a s-graph of a circut---'
    vertex_set_dict={}
    vertex_set=[]
    edge_set=[]
    edge_set2=[]
    clock_set=[]
    PI_edge=[]
    PO_edge=[]
    # ----------vertex
    for eachPPort in m_list[0].port_list:
        if eachPPort.port_type=='input':
            vertex_set_dict[eachPPort.port_name]="P"+eachPPort.port_type[0].upper()
            vertex_set.append(eachPPort.port_name)
    for eachModule in m_list[1:]:
        vertex_set_dict[eachModule.name]=eachModule.m_type
        vertex_set.append(eachModule.name)
    for eachPPort in m_list[0].port_list:
        if eachPPort.port_type=='output':
            vertex_set_dict[eachPPort.port_name]="P"+eachPPort.port_type[0].upper()
            vertex_set.append(eachPPort.port_name)    
    #-----------PI PO edge excluding clock and  reset
    for eachModule in m_list[1:]:
        for eachPort in eachModule.port_list:
            if (eachModule.m_type=='FD' and (re.match('[DQ]',eachPort.port_name) is None)):
                continue
            else:
                for eachPPort in m_list[0].port_list:
                    if re.match(eachPort.port_assign,eachPPort.port_name) is not None:
                        if eachPPort.port_type=='input':
                            PI_edge.append([eachPPort.port_name,eachModule.name])
                        else:
                            PO_edge.append([eachModule.name,eachPPort.port_name])
    #----------ALL other Module
    for eachModule in m_list[1:]:
        for eachPort in eachModule.port_list:
            if eachPort.port_type=='clock' and (not eachPort.port_assign in clock_set):
                clock_set.append(eachPort.port_assign)
            elif (eachModule.m_type=='FD' and (re.match('[DQ]',eachPort.port_name) is None)):
                continue
            else:
                for eachModule2 in m_list[1:]:
                    for eachPort2 in eachModule2.port_list:
                        if (eachModule.m_type=='FD' and (re.match('[DQ]',eachPort.port_name) is None)):
                            continue
                        elif (eachModule==eachModule2 and eachPort==eachPort2):
                            continue
                        elif eachPort2.port_assign==eachPort.port_assign:
                            if (eachPort.port_type=='input' and eachPort2.port_type=='output'):
                                if [m_list.index(eachModule2),m_list.index(eachModule)] not in edge_set:
                                    edge_set2.append([eachModule2.name,eachModule.name])
                                    edge_set.append([m_list.index(eachModule2),m_list.index(eachModule)])
                            elif (eachPort.port_type=='output' and eachPort2.port_type=='input'):
                                if [m_list.index(eachModule),m_list.index(eachModule2)] not in edge_set:
                                    edge_set2.append([eachModule.name,eachModule2.name])
                                    edge_set.append([m_list.index(eachModule),m_list.index(eachModule2)])
    
    edge_set2=edge_set2+PI_edge+PO_edge
    if verbose:
        print '-----------------------------------------------'
        print 'Info:vertex_set ARE:'
        i=1
        for eachVertex in m_list[1:]:
            print str(i)+':'+eachVertex.name+':'+eachVertex.m_type
            i=i+1
        print '-----------------------------------------------'
        print 'Info:edge_set   ARE:'
        for eachEdge in edge_set:
            print eachEdge
        print '-----------------------------------------------'
        print 'Info:clock_set  ARE:'
        for eachClock in clock_set:
            print eachClock   
    print 'Note: get_edge_vertex() successfully !'
    return vertex_set,vertex_set_dict,edge_set,edge_set2,PI_edge,PO_edge
###############################################################################
def safe_remove(sequence,element):
    if element in sequence:
        sequence.remove(element)
    else:
        pass
    return True

###############################################################################
def construct_s_graph(edge_set2,vertex_set,vertex_set_dict):

    #delet the no FD edge in this grapgh
    edge_set_cpy=copy.deepcopy(edge_set2)  
    vertex_set_cpy=copy.deepcopy(vertex_set)    
    for eachVertex in vertex_set:    
        if  not vertex_set_dict[eachVertex] in ['FD', 'PI','PO']:
            for eachEdge in edge_set2:
                if eachVertex==eachEdge[0]:
                    safe_remove(edge_set_cpy,eachEdge)
                    for eachEdge2 in edge_set2:
                        if eachVertex==eachEdge2[1]:
                            safe_remove(edge_set_cpy,eachEdge2)
                            edge_set_cpy.append([eachEdge2[0],eachEdge[1]])
            vertex_set_cpy.remove(eachVertex) 
    print 'Info: s_vertex:-----------------------------------------------------'
    for eachVertex in vertex_set_cpy:
        print eachVertex+'::::'+vertex_set_dict[eachVertex]
    print 'Info: s_edge  :-----------------------------------------------------'
    for eachEdge in edge_set_cpy:
        print str(eachEdge)+"::::["+vertex_set_dict[eachEdge[0]]+"-->>"+vertex_set_dict[eachEdge[1]]+']'
#    for eachEdge in edge_set:    
#        ####record the source_node and destiny_node of eachEdge
#        ####in case you delete the Edge and the info was deleted
#        s_node=eachEdge[0]
#        d_node=eachEdge[1]
#        if m_list[eachEdge[0]].m_type!="FD" and m_list[eachEdge[1]].m_type=="FD":
#            safe_remove(edge_set_cpy,eachEdge)
#            for edge2 in edge_set:
#                if edge2[1]==s_node:
#                    safe_remove(edge_set_cpy,edge2)
#                    edge_set_cpy.append([edge2[0],eachEdge[1]])
#        elif m_list[eachEdge[1]].m_type!="FD" and m_list[eachEdge[0]].m_type!="FD":
#            safe_remove(edge_set_cpy,eachEdge)
#            for edge2 in edge_set:
#                if edge2[1]==s_node:
#                    safe_remove(edge_set_cpy,edge2)
#                    for edge3 in edge_set:
#                        if edge3[0]==d_node:                                                    
#                            safe_remove(edge_set_cpy,edge3)
#                            edge_set_cpy.append([edge2[0],edge3[1]])
#                elif edge2[0]==d_node:
#                    safe_remove(edge_set_cpy,edge2)
#                    for edge3 in edge_set:
#                        if edge3[1]==s_node:
#                            safe_remove(edge_set_cpy,edge3)
#                            edge_set_cpy.append([edge3[0],edge2[1]])
#        elif m_list[eachEdge[0]].m_type=="FD" and m_list[eachEdge[1]].m_type!="FD":
#            safe_remove(edge_set_cpy,eachEdge)
#            for edge2 in edge_set:
#                if edge2[0]==d_node:
#                    safe_remove(edge_set_cpy,edge2)
#                    edge_set_cpy.append([eachEdge[0],edge2[1]])
    return edge_set_cpy,vertex_set_cpy
###############################################################################
def visualize_s_graph(vertex_set,edge_set,fname):
    graph=nx.DiGraph()
    graph.add_nodes_from(vertex_set)
    graph.add_edges_from(edge_set)
    nx.draw_spring(graph)            
    print nx.info(graph)
    plt.savefig(fname+".png")
    plt.show()
    return True

###############################################################################
def calc_logic_depth(all_edge_set,m_list,vertex_set_dict):
    graph=nx.DiGraph()
    graph.add_edges_from(all_edge_set)
    logic_depth_dict={}
    for eachNode in vertex_set_dict.keys():
        #get the depth of all nodes
        if vertex_set_dict[eachNode]=='FD':
            tmp=[]
            for eachPI in m_list[0].port_list:
                if eachPI.port_type=='input':               
                    depth=nx.shortest_path_length(graph,source="pi"+eachPI.port_name,target=eachNode)
                    tmp.append(depth)
            logic_depth=min(depth for depth in tmp)
            logic_depth_dict[eachNode]=logic_depth
            print "Node"+eachNode+"_depth: "+str(logic_depth)        
    return logic_depth_dict
    
###############################################################################
if __name__=="__main__":
    fname=raw_input("plz enter filename:")
    signal_list,m_list,defparam_init_list=nu.extract_m_list(fname,verbose=False)
    vertex_set,vertex_set_dict,edge_set,edge_set2,PI_edge,PO_edge=get_edge_vertex(m_list,verbose=True)
    s_edge,s_vertex=construct_s_graph(edge_set2,vertex_set,vertex_set_dict)   
#    all_edge_set=edge_set2+PI_edge+PO_edge
#    all_edge_set=edge_set
#    fobj=open(fname[:-3]+'_eg.txt','w')
#    fobj2=open(fname[:-3]+'_vet.txt','w')
#    for eachEdge in edge_set:
#        fobj.writelines(str(eachEdge[0])+' '+str(eachEdge[1])+'\n')
#    for eachVertex in vertex_set_dict.keys():
#        fobj2.writelines(eachVertex+':::::'+vertex_set_dict[eachVertex]+'\n')
    visualize_s_graph(s_vertex,s_edge,fname)
#    logic_depth_dict=calc_logic_depth(all_edge_set,m_list,vertex_set_dict)
#    fobj.close()
#    fobj2.close()
    