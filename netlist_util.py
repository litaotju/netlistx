# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 16:30:03 2015
@author: litao
"""
'--this file is composed of a lot of functions to parse and util the Src file--'
import os
import copy
import generate_testbench as gt
import file_util as fu
###############################################################################
def get_all_fd(m_list,verbose=False):
    '--get all the FD and its D_Q port--'
    all_fd_dict={}
    if verbose:
        print '-----------------------------------------'
        print 'Note:all the FD and its D port assign Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='FD':
            port_info={}
            for eachPort in eachModule.port_list:
                if eachPort.port_name=='D':
                    port_info['D']=eachPort.port_assign
                elif eachPort.port_name=='C':
                    port_info['C']=eachPort.port_assign
                elif eachPort.port_name=='Q':
                    port_info['Q']=eachPort.port_assign
                elif eachPort.port_name=='CE':
                    port_info['CE']=eachPort.port_assign
                elif eachPort.port_name=='CLR':
                    port_info['CLR']=eachPort.port_assign
            all_fd_dict[eachModule.name]=port_info
            if verbose:
                print eachModule.name +str(port_info)
    print "Note: get_all_fd() sucessfully !"
    return all_fd_dict
###############################################################################
def get_all_lut(m_list,lut_type_cnt,verbose=False):
    all_lut_dict={} 
    if verbose:
        print '-----------------------------------------'
        print 'Info: all the LUT and its name Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='LUT':
            #record eachLUT's name and its type
            all_lut_dict[eachModule.name]=eachModule.cellref
            lut_kind=int(eachModule.cellref[3])-1
            lut_type_cnt[lut_kind]=lut_type_cnt[lut_kind]+1 
    assert len(all_lut_dict.keys())==sum(lut_type_cnt),'Assertion Error: LUT cnt error'
    return all_lut_dict
    
    
###############################################################################
def get_lut_cnt2_FD(m_list,all_fd_dict,verbose,K=6):
    '--get all the module that has a connection to a FDs D port--'
    #to parent function
    FD_din_lut_list=[]
    lut_out2_FD_dict={}
    if verbose:
        print '-----------------------------------------------------'
        print 'Note:all the Lut has output connect to FD\'s .D port Are:'
    for each_FD in all_fd_dict.keys():   
        for eachModule in m_list[1:]:
            if eachModule.m_type=='LUT' and eachModule.been_searched==False :
                if eachModule.port_list[-1].port_assign==all_fd_dict[each_FD]['D']\
                    and int(eachModule.cellref[3])<=(K-2):
                        eachModule.been_searched=True
                        FD_din_lut_list.append(each_FD)
                        lut_out2_FD_dict[eachModule.name]=[int(eachModule.cellref[3]),each_FD]
                        if verbose:
                            print '%s.D <--- %s %s'%(each_FD,eachModule.cellref,eachModule.name)                       
            else:
                continue
    print 'Note: get_lut_cnt2_FD() successfully !'
    return lut_out2_FD_dict,FD_din_lut_list
###############################################################################
def get_clk_in_fd(all_fd_dict,verbose):
    clock_list=[]
    ##原来的版本是从m_list从提取,现在只需要从all_fd_dict中提取就好了
#    for eachModule in m_list[1:]:
#        if eachModule.name in all_fd_list:
#            for eachPort in eachModule.port_list:
#                if eachPort.port_type=="clock":
#                    if eachPort.port_assign not in clock_list:
#                        clock_list.append(eachPort.port_assign)
#                    else:
#                        continue
    for eachFD in all_fd_dict.keys():
        assert all_fd_dict.has_key("C"),"Error:FD %s has no C port" % eachFD
        current_clk=all_fd_dict[eachFD]['C']
        if current_clk not in clock_list:
            clock_list.append(current_clk)
    assert len(clock_list)==1,\
        "Warning: has >1 clock domain. clock cnt is %d" % len(clock_list)
    if verbose:
        print "Info:all clock signals are as follows:"
        for clock in  clock_list:
            print clock
    print "Note: get_all_clock() successfully !"
    return clock_list
    
###############################################################################   
def get_ce_in_fd(all_fd_dict,verbose):
    ce_signal_list=[]
    fd_has_ce_list=[]
    for eachFD in all_fd_dict.keys():
         if all_fd_dict[eachFD].has_key('CE'):
             fd_has_ce_list.append(eachFD)
             current_ce=all_fd_dict[eachFD]['CE']
             if current_ce not in ce_signal_list:
                 ce_signal_list.append(current_ce)
    if verbose:
        print "Note:all ce signal are as follows:"
        for ce in ce_signal_list:    
            print ce
    print"Note: get_ce_in_fd() successfully !"
    return ce_signal_list,fd_has_ce_list
    
###############################################################################
def get_lut_cnt2_ce(m_list,ce_signal_list,K=6,verbose=False):
    "get for lut combine for ce signal"
    lut_cnt2_ce=[]
    
    opt_ce_flag=False
    un_opt_ce_list=copy.deepcopy(ce_signal_list)
    for eachCE in ce_signal_list:
        for eachModule in m_list[1:]:
            if eachModule.m_type=="LUT" and  eachModule.been_searched==False :
                if eachModule.port_list[-1].port_assign==eachCE \
                and int(eachModule.cellref[3])<=(K-1):
                    eachModule.been_searched=True
                    opt_ce_flag=True
                    lut_cnt2_ce.append(eachModule.name)
        if opt_ce_flag==True:
            un_opt_ce_list.remove(eachCE)
            opt_ce_flag=False                 
    if verbose:
        for x in lut_cnt2_ce:
            print x
    print "Note: get_lut_cnt2_ce() !"
    return lut_cnt2_ce,un_opt_ce_list
    
###############################################################################  
if __name__=='__main__':
    print "Current PATH is:"+os.getcwd()
    print [file for file in os.listdir(os.getcwd())]    
    fname=raw_input('plz enter the file name:') 
    K=int(raw_input('plz enter the K parameter of FPGA:K='))
    signal_list,m_list,defparam_list=fu.extract_m_list(fname,True)
    all_fd_dict=get_all_fd(m_list,False)
    lut_out2_FD_dict,FD_din_lut_list=get_lut_cnt2_FD(m_list,all_fd_dict,True,K)
    ce_signal_list=get_ce_in_fd(all_fd_dict,False)
    clock_signal_list=get_clk_in_fd(all_fd_dict,verbose=True)
    gt.generate_testbench(m_list[0],len(all_fd_dict),os.getcwd())



                

