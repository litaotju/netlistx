# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:27:23 2015
@author: litao
"""
import networkx as nx
import os.path
import netlist_util as nu
###############################################################################
def get_edge_vertex(m_list,verbose=False):
    '---this func is to construct a s-graph of a circut---'
    vertex_set_dict={}
    vertex_set2=[]
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
                    vertex_set_dict[eachPPort.port_name+'['+str(i)+']']="P"+eachPPort.port_type[0].upper()
            else:
                vertex_set_dict[eachPPort.port_name]="P"+eachPPort.port_type[0].upper()                
                PI_vertex.append(eachPPort.port_name)
    #------------module vertex
    for eachModule in m_list[1:]:
        vertex_set_dict[eachModule.name]=eachModule.m_type
        vertex_set2.append(eachModule.name)
    #------------PO vertex
    for eachPPort in m_list[0].port_list:
        if eachPPort.port_type=='output':
            if eachPPort.port_width>1:           
                for i in range(0,eachPPort.port_width):
                    PO_vertex.append(eachPPort.port_name+'['+str(i)+']')                   
                    vertex_set_dict[eachPPort.port_name+'['+str(i)+']']="P"+eachPPort.port_type[0].upper()
            else:
                vertex_set_dict[eachPPort.port_name]="P"+eachPPort.port_type[0].upper()
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
    module_edge=edge_set2
    edge_set=[PI_edge,module_edge,PO_edge]
    module_vertex=vertex_set2
    vertex_set=[PI_vertex,module_vertex,PO_vertex]
    ###########################################################################
    #--------print info part 
#    if verbose:
#        print 'Info:vertex number is: %d'% len(vertex_set)
#        print 'Info:vertex_set ARE:--------------------------------------------'
#        for eachVertex in vertex_set:
#            print  vertex_set_dict[eachVertex]+'::::'+eachVertex
#        print 'Info:edge   number is: %d'% len(edge_set2)        
#        print 'Info:edge_set   ARE:--------------------------------------------'
#        for eachEdge in edge_set2:
#            print vertex_set_dict[eachEdge[0]]\
#                    +"-->>"+vertex_set_dict[eachEdge[1]]+"::::"+str(eachEdge)
    print 'Note: get_edge_vertex() successfully !'
    return vertex_set,vertex_set_dict,edge_set
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
#if __name__=="__main__":
#    parent_path=os.getcwd()+"\\test_input_netlist\\bench_virtex4" 
#    for eachFile in os.listdir(parent_path):
#        print  eachFile
#        if  os.path.splitext(eachFile)[1]=='.v':
#            fname=os.path.join(parent_path,eachFile)
##    fname=raw_input("plz enter filename:")
#            signal_list,m_list,defparam_init_list       = nu.extract_m_list(fname,verbose=False)
#            graph,vertex_set,vertex_set_dict,edge_set2  = get_edge_vertex(m_list,verbose=False)
#            s_graph,s_edge,s_vertex                     = construct_s_graph(edge_set2,vertex_set,\
#                                                            vertex_set_dict,verbose=False)   
##   s_graph=construct_s_graph_new(graph,vertex_set_dict,verbose=True)
##   visualize_s_graph(s_vertex,vertex_set_dict,s_edge,fname,display_pipo=False)
##   logic_depth_dict=calc_logic_depth(s_graph,vertex_set_dict)    
#    #########################################################################                                                
#            ###setup output file dir输出设置
#            name_base=os.path.splitext(eachFile)
#            output_dir=os.getcwd()+"\\test_output_dir\\vertex_edge\\"   
#            fobj=open(output_dir+name_base[0]+'_eg.txt','w')
#            fobj2=open(output_dir+name_base[0]+'_vet.txt','w')
#            for eachEdge in s_edge:
#                fobj.writelines(str(eachEdge[0])+' '+str(eachEdge[1])+'\n')
#            for eachVertex in s_vertex:
#               fobj2.writelines(eachVertex+':::::'+vertex_set_dict[eachVertex]+'\n')
#            fobj.close()
#            fobj2.close()
#            print name_base+" extract s_graph successfully."
###############################################################################    
    
    