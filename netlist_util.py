# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 16:30:03 2015
@author: litao
"""
'--this file is composed of a lot of functions to parse and util the Src file--'
import os, re ,copy
import testbench_generate as gt

###############################################################################
def vm_parse(input_file):
    from netlist_parser.netlist_parser import parser
    '''returns info of input vm file as a list,
        info[0] is a instance of cc.circut_module which is top_module in vm,
        info[1] is the input_ouput decl list of vm file,
        info[2] is the wire        decl list,
        info[3] is the primitive instances(cc.circut_module obj) list,and the defparam of primitive(if exist)
        info[4] is the assign list of a file 
    '''
    try:
        fobj=open(input_file,'r')
    except IOError,e:
        print "Error: file open error:",e
        return None
    else:
        all_lines=fobj.read()
        fobj.close()
        p=parser.parse(all_lines)
        #--------------------------------
        #打印部分
        #--------------------------------
    #    console=sys.stdout
    #    sys.stdout=fobj2
    #    p[0].print_module()
    #    for eachPort_decl in p[1]:
    #        eachPort_decl.__print__(pipo_decl=True)
    #    for eachSignal in p[2]:
    #        eachSignal.__print__(is_wire_decl=True)
    #    for eachPrimitive in p[3]:
    #        eachPrimitive.print_module()
    #    if len(p)==5:
    #        assign_stm_list=p[4]
    #        for eachAssign in p[4]:
    #            eachAssign.__print__()
    #    print "endmodule;"
    #    sys.stdout=console
        #------------------------------------
        #解析完完全打印出来
        #------------------------------------
        parser.restart()
        print "Job: parse the vm file %s finished."% input_file
        return p

###############################################################################
def mark_the_circut(m_list,allow_dsp=False,allow_unkown=True,verbose=False):
    'mark all the module with a type'
    cellref_list=[]
    for eachModule in m_list[1:]:
        if eachModule.cellref not in cellref_list:
            cellref_list.append(eachModule.cellref)
        #FD--------------------------------------------------------------------
        if re.match('FD\w*',eachModule.cellref) is not None:
            eachModule.m_type='FD'
            for eachPort in eachModule.port_list:
                if eachPort.port_name=='D':
                    eachPort.port_type='input'
                elif eachPort.port_name=='Q':
                    eachPort.port_type='output'
                elif eachPort.port_name=='C':
                    eachPort.port_type='clock'
                elif eachPort.port_name=='CE':
                    eachPort.port_type='input'
                else:
                    eachPort.port_type='input'
        
        # LUT------------------------------------------------------------------
        elif re.match('LUT\w+',eachModule.cellref) is not None:
            eachModule.m_type='LUT'
            for eachPort in eachModule.port_list:
                if eachPort.port_name[0]=='I':
                    eachPort.port_type='input'
                else:
                    assert eachPort.port_name in ['O','LO','O5','O6'],\
                        eachModule.cellref+"  "+eachModule.name+"  "+eachPort.port_name
                    eachPort.port_type='output'

        # MUX and XOR----------------------------------------------------------
        elif re.match('MUX\w+|XOR\w+|INV|MULT_AND',eachModule.cellref) is not None:
            eachModule.m_type=eachModule.cellref
            for eachPort in eachModule.port_list[:-1]:
                eachPort.port_type='input'
            eachModule.port_list[-1].port_type='output'
            
        #BUF------------------------------------------------------------------
        elif re.match('\w*BUF\w*',eachModule.cellref) is not None:
            eachModule.m_type='BUF'
            for eachPort in eachModule.port_list:
                assert eachPort.port_name in ['I','O'],\
                    "BUF:%s has a port neither I or O" %eachModule.name
                if eachPort.port_name=='I':
                    eachPort.port_type='input'
                elif eachPort.port_name=='O':
                    eachPort.port_type='output'
        #GND VCC---------------------------------------------------------------
        elif (eachModule.cellref=='GND' or eachModule.cellref=='VCC'):
            eachModule.m_type=eachModule.name
            assert len(eachModule.port_list)==1
            for eachPort in eachModule.port_list:
                eachPort.port_type='output'

        #DSP48E---------------------------------------------------------------
        elif re.match('DSP48|DSP48E\w*',eachModule.cellref) is not None:
            eachModule.m_type='DSP'
            if not allow_dsp:
                raise AssertionError,"Warning:find %s : %s in this netlist"\
                    %(eachModule.cellref,eachModule.name)
            else:
                print "Warning:find %s : %s in this netlist"\
                        %(eachModule.cellref,eachModule.name)
        else:
            if not allow_unkown:
                raise AssertionError,\
                 'Error:unknown cellref:'+eachModule.cellref+"  "+eachModule.name+'\n'+\
                      "plz update the mark_the_circut() to keep this programe pratical"
            else:
                print 'Warning:unknown cellref:'+eachModule.cellref+"  "+eachModule.name+'\n'+\
                      "plz update the mark_the_circut() to keep this programe pratical"
    if verbose:        
        print 'Note:module list is:'
        for eachModule in m_list:
            eachModule.__print__()    
    print "Note: mark_the_circut() successfully !"
    return cellref_list

###############################################################################
def get_all_fd(m_list,verbose=False):
    '--get all the FD and its D_Q port--'
    all_fd_dict={}
    if verbose:
        print 'Info: all the FD and its D port assign Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='FD':
            port_info={}
            for eachPort in eachModule.port_list:
                port_info[eachPort.port_name]=eachPort.port_assign
            all_fd_dict[eachModule.name]=port_info
            if verbose:
                print eachModule.name
                for eachPort in port_info.keys():
                    print eachPort,
                    port_info[eachPort].__print__()
                print '\n'
    print "Note: get_all_fd() sucessfully !"
    return all_fd_dict
###############################################################################
def get_all_lut(m_list,lut_type_cnt,verbose=False):
    all_lut_dict={} 
    if verbose:
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
        print 'Info: all the Lut has output connect to FD\'s .D port Are:'
    for each_FD in all_fd_dict.keys():   
        for eachModule in m_list[1:]:
            if eachModule.m_type=='LUT' and eachModule.been_searched==False :
                if eachModule.port_list[-1].port_assign.string==all_fd_dict[each_FD]['D'].string\
                    and int(eachModule.cellref[3])<=(K-2):
                        eachModule.been_searched=True
                        FD_din_lut_list.append(each_FD)
                        lut_out2_FD_dict[eachModule.name]=[int(eachModule.cellref[3]),each_FD]
                        if verbose:
                            print '%s.D <--- %s %s'%(each_FD,eachModule.cellref,eachModule.name)                       
            else:
                continue
    print '\nNote: get_lut_cnt2_FD() successfully !'
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
        assert all_fd_dict[eachFD].has_key("C"),"Error:FD %s has no C port" % eachFD
        current_clk=all_fd_dict[eachFD]['C'].string
        if current_clk not in clock_list:
            clock_list.append(current_clk)
    assert len(clock_list)==1,\
        "Warning: has %d clock domain" % len(clock_list)
    if verbose:
        print "Info:all clock signals are as follows:"
        for clock in  clock_list:
            print clock+",",
        print '\n'
    print "Note: get_all_clock() successfully !"
    return clock_list
    
###############################################################################   
def get_ce_in_fd(all_fd_dict,verbose):
    ce_signal_list=[]
    fd_has_ce_list=[]
    for eachFD in all_fd_dict.keys():
         if all_fd_dict[eachFD].has_key('CE'):
             fd_has_ce_list.append(eachFD)
             current_ce=all_fd_dict[eachFD]['CE'].string
             if current_ce not in ce_signal_list:
                 ce_signal_list.append(current_ce)
    if verbose:
        if ce_signal_list:
            print "Info: all ce signal are as follows:"
            for ce in ce_signal_list:    
                print ce
        else:
            print "Info: no ce found in netlist"
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
                if eachModule.port_list[-1].port_assign.string==eachCE \
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
    '--the test func of this module--'
    import netlist_parser.netlist_parser     as np
    verbose=False
    gene_tb=False
    print "Current PATH is:"+os.getcwd() 
    fname=raw_input('plz enter the file name:') 
    K=int(raw_input('plz enter the K parameter of FPGA:K='))  
    info=np.vm_parse(fname)
    signal_list=info['signal_decl_list']
    m_list=info['m_list']
    mark_the_circut(m_list,True,verbose)    
    all_fd_dict=get_all_fd(m_list,verbose)
    lut_out2_FD_dict,FD_din_lut_list=get_lut_cnt2_FD(m_list,all_fd_dict,verbose,K) 
    ce_signal_list=get_ce_in_fd(all_fd_dict,verbose)
    clock_signal_list=get_clk_in_fd(all_fd_dict,verbose=verbose)
    if gene_tb:
        gt.generate_testbench(m_list[0],len(all_fd_dict),os.getcwd())



                

