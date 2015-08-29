# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 16:30:03 2015
@author: litao
this file is composed of a lot of functions to parse and util the netlist Src file
"""

import os, re, copy
###############################################################################
def vm_parse(input_file):
    '''returns info of input vm file as a dict
    '''
    from netlist_parser.netlist_parser import parser
    try:
        fobj=open(input_file,'r')
    except IOError,e:
        print "Error: file open error:",e
        exit()
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
        print "Note: parse the netlist file %s finished."% input_file
        return p

###############################################################################
def mark_the_circut(m_list,allow_dsp=False,allow_unkown=True,verbose=False):
    'mark all the module with a type'
    cellref_list=[]
    FD_TYPE=('FDCE','FDPE','FDRE','FDSE','FDC','FDP','FDR','FDS','FDE', 'FD')
    LUT_TYPE=('LUT1','LUT2','LUT3','LUT4','LUT5','LUT6',
              'LUT1_L','LUT2_L','LUT3_L','LUT4_L','LUT5_L','LUT6_L',
              'LUT6_2')
    OTHER_COMBIN=('MUXCY','MUXCY_L','MUXF7','MUXF8','XORCY','INV','MULT_AND','MUXF5',
                  'MUXF6')
    for eachModule in m_list[1:]:
        if eachModule.cellref not in cellref_list:
            cellref_list.append(eachModule.cellref)
        #FD--------------------------------------------------------------------
        if re.match('FD\w*',eachModule.cellref) is not None:
            assert eachModule.cellref in FD_TYPE,\
                "%s ,%s not in predefined FD_TYPE"%(eachModule.cellref,eachModule.name)
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
            assert eachModule.cellref in LUT_TYPE,\
                "%s ,%s not in predefined LUT_TYPE"%(eachModule.cellref,eachModule.name)
            for eachPort in eachModule.port_list:
                if eachPort.port_name[0]=='I':
                    eachPort.port_type='input'
                else:
                    assert eachPort.port_name in ['O','LO','O5','O6'],\
                        eachModule.cellref+"  "+eachModule.name+"  "+eachPort.port_name
                    eachPort.port_type='output'

        # MUX and XOR----------------------------------------------------------
        elif eachModule.cellref in OTHER_COMBIN:
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
            eachModule.m_type=eachModule.cellref
            assert len(eachModule.port_list)==1
            for eachPort in eachModule.port_list:
                eachPort.port_type='output'

        #DSP48E---------------------------------------------------------------
        elif re.match('DSP48|DSP48E\w*',eachModule.cellref) is not None:
            eachModule.m_type='DSP'
            if not allow_dsp:
                raise AssertionError,"Error:find %s : %s in this netlist"\
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
        print 'Info: module list is:'
        for eachModule in m_list:
            eachModule.__print__()    
    print "Note: mark_the_circut() successfully !"
    return cellref_list

###############################################################################
def get_all_fd(m_list,verbose=False):
    '--get all the FD and its D_Q port--'
    all_fd_dict={}
    if verbose:
        print 'Info: all the FD and its port_assign.string are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='FD':
            port_info={}
            for eachPort in eachModule.port_list:
                port_info[eachPort.port_name]=eachPort.port_assign
            assert not all_fd_dict.has_key(eachModule.name),\
                "%s:%s"%(eachModule.cellref,eachModule.name)
            all_fd_dict[eachModule.name]=port_info
            if verbose:
                print "%s %s :"%(eachModule.cellref,eachModule.name),
                for eachPort in port_info.keys():
                    print ".%s(" % eachPort,
                    port_info[eachPort].__print__()
                    print ") ",
                print '\n'
    print "Note: get_all_fd() sucessfully !"
    return all_fd_dict
###############################################################################
def get_all_lut(m_list,lut_type_cnt=[0]*6,verbose=False):
    ''''get_all_lut(m_list,lut_type_cnt,verbose)
        ->>the all_lut_dict,key is name, calue is cellref and port_info'''
    all_lut_dict={} 
    if verbose:
        print 'Info: all the LUT and its name Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='LUT':
            if verbose:
                print "%s:%s"%(eachModule.cellref,eachModule.name)
            port_info={}
            for eachPort in eachModule.port_list:
                port_info[eachPort.port_name]=eachPort.port_assign
            assert not all_lut_dict.has_key(eachModule.name),"%s:%s"%\
                (eachModule.cellref, eachModule.name)
            all_lut_dict[eachModule.name]=[eachModule.cellref,port_info]
            lut_kind=int(eachModule.cellref[3])-1
            lut_type_cnt[lut_kind]=lut_type_cnt[lut_kind]+1 
    assert len(all_lut_dict.keys())==sum(lut_type_cnt),'Assertion Error: LUT cnt error'
    return all_lut_dict
    
    
###############################################################################
def get_lut_cnt2_FD(m_list,all_fd_dict,verbose=False,K=6):
    'get all the LUT that has a connection to a FDs D port'
    FD_din_lut_list=[]
    lut_out2_FD_dict={}
    if verbose:
        cnt=0
        print 'Info: all the Lut has output connect to FD\'s .D port Are:'
    for each_FD in all_fd_dict.keys():  
        cuurent_d_assign=all_fd_dict[each_FD]['D'].string
        for eachModule in m_list[1:]:       
            if eachModule.m_type=='LUT' and  int(eachModule.cellref[3])<=(K-2) \
                    and eachModule.been_searched==False :
                ##一般来讲，取最后一个LUT的端口作为输出是对的，但是对于LUT6_2的情况，有O5,O6两个端口
                ##但是对于LUT6_2来讲，这些都不重要，因为永远不会连接到LUT6_2.只记录了有小于K-2个端口的LUT
                assert eachModule.port_list[-1].port_name in ['O','LO']
                current_lut_out=eachModule.port_list[-1].port_assign.string
                if current_lut_out==cuurent_d_assign:
                    eachModule.been_searched=True
                    FD_din_lut_list.append(each_FD) 
                    lut_out2_FD_dict[eachModule.name]=[int(eachModule.cellref[3]),each_FD]
                    if verbose:
                        print '%s.D <--- %s %s'%(each_FD,eachModule.cellref,eachModule.name)
                        cnt=cnt+1                    
                    #一个FD的端口最多只能连接到一个LUT的输出上面，所以找到之后跳出循环，进行下一个FD
                    break
    if verbose:
        print "Info: found %d (K-2)LUT connected to FD's D port."% cnt
    print 'Note: get_lut_cnt2_FD() successfully !'
    return lut_out2_FD_dict,FD_din_lut_list
###############################################################################
def get_clk_in_fd(all_fd_dict,verbose=False):
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
    assert len(clock_list)<=1,\
        "AssertError: has %d clock domain\n %s " % (len(clock_list),\
            ",".join(clock_list) )
    if verbose:
        print "Info:all clock signals are as follows:\n    ",
        for clock in  clock_list:
            print clock
    print "Note: get_all_clock() successfully !"
    return clock_list
    
###############################################################################   
def get_ce_in_fd(all_fd_dict,verbose=False):
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
            print "Info: all ce signal are as follows:\n    ",
            for ce in ce_signal_list:    
                print ce
        else:
            print "Info: no ce found in netlist"
    print"Note: get_ce_in_fd() successfully !"
    return ce_signal_list,fd_has_ce_list
###############################################################################
#featured 7.15
def get_reset_in_fd(all_fd_dict,verbose=False):
    'get all the async and sync reset of all fd in this m_list'
    async_reset_list=[]    
    reset_list=[]    
    for eachFD in all_fd_dict.keys():
        if all_fd_dict[eachFD].has_key('CLR'):
            current_asyn_reset_assign=all_fd_dict[eachFD]['CLR'] #its a cc.signal obj
            current_asyn_reset=current_asyn_reset_assign.string  #get its string attr as unique
            if current_asyn_reset not in async_reset_list:
                async_reset_list.append(current_asyn_reset)
        elif all_fd_dict[eachFD].has_key('PRE'):
            current_asyn_reset_assign=all_fd_dict[eachFD]['PRE'] #its a cc.signal obj
            current_asyn_reset=current_asyn_reset_assign.string  #get its string attr as unique
            if current_asyn_reset not in async_reset_list:
                async_reset_list.append(current_asyn_reset)
        elif all_fd_dict[eachFD].has_key('R'):
            current_reset_assign=all_fd_dict[eachFD]['R']
            current_reset=current_reset_assign.string
            if current_reset not in reset_list:
                reset_list.append(current_reset)
        elif all_fd_dict[eachFD].has_key('S'):
            current_reset_assign=all_fd_dict[eachFD]['S']
            current_reset=current_reset_assign.string
            if current_reset not in reset_list:
                reset_list.append(current_reset)
    if verbose:
        print "Info: all the Async Reset Signal Are:\n    ",
        for eachAsync in async_reset_list:
            print eachAsync+",  "
        print "\nInfo: all the Sync Reset Signal Are:\n    ",
        for eachSync  in reset_list:
            print eachSync +",  "
    print "Note: get_reset_in_fd() successfully"
    return reset_list,async_reset_list
    
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
#featured 7.15    
def rules_check(m_list):
    '''保证只有一个时钟域，保证时钟和复位信号都是通过外部引脚进行控制的。
    ''' 
    print "Process: check rules of netlist to construct graph..."
    special_signal = {}
    print "Process: finding all fd in netlist..."
    all_fd_dict = get_all_fd(m_list)
    print "Process: finding all clks connect to fd..."
    clock_signal = get_clk_in_fd(all_fd_dict, True)
    print "Process: finding all reset and async reset of fd..."
    reset_list, async_reset_list = get_reset_in_fd(all_fd_dict, True)
    ##注意一个潜在的问题，只有网表的端口宽度为1时，也就是信号与string相同时，规则检查才有效
    single_bit_pi = []
    if len(clock_signal) == 1 : # 时钟个数为0时 ， 不用检查时钟了
        clock_flag = False    
        for eachPi in m_list[0].port_list:
            if eachPi.port_type == 'input' and eachPi.port_width == 1:
                if clock_signal[0] == eachPi.name:
                    clock_flag = True
                single_bit_pi.append(eachPi.name)
        if not clock_flag:
            raise AssertionError,"CLOCK signal is not cnnected to any PI"
    for anyReset in reset_list:
        if not anyReset in single_bit_pi:
            raise AssertionError,"Reset signal %s not connected to any PI"% anyReset
    for anyAsyncReset in async_reset_list:
        if not anyAsyncReset in single_bit_pi:
            raise AssertionError,"Async Reset signal %s not connected to any PI"% anyAsyncReset
    special_signal={ 'CLOCK':clock_signal,
                    'SYNC_RESET':reset_list,
                    'ASYNC_RESET':async_reset_list}
    print "Info: Rules check successfully, no rules vialation to model with a graph"
    return special_signal
###############################################################################  
if __name__=='__main__':
    'the test func of this module'
    import sys
    ##单个文件测试
    if len(sys.argv)==1:
        verbose=False
        gene_tb=False
        print "Current PATH is:"+os.getcwd()
        cellref_set=set()
        fname=raw_input('plz enter the file name:') 
        K=int(raw_input('plz enter the K parameter of FPGA:K='))
        ##网表解析与后续标记
        info=vm_parse(fname)
        signal_list=info['signal_decl_list']
        m_list=info['m_list']
        cellref_list=mark_the_circut(m_list,allow_dsp=True,allow_unkown=False,verbose=False)
        cellref_set=cellref_set|(set(cellref_list))
        print "All the primitibve type in file are:"
        for eachCellref in cellref_set:
            print eachCellref        
        ##获取D触发器和LUT信息,的测试 
        
        lut_type_cnt=[0]*6    
        all_fd_dict=get_all_fd(m_list,verbose)
        all_lut_dict=get_all_lut(m_list,lut_type_cnt,verbose)
        lut_out2_FD_dict,FD_din_lut_list=get_lut_cnt2_FD(m_list,all_fd_dict,verbose,K) 
        ##D触发器的特殊信号 
        ce_signal_list             =get_ce_in_fd(all_fd_dict,verbose)
        clock_signal_list          =get_clk_in_fd(all_fd_dict,verbose)
        reset_list,async_reset_list=get_reset_in_fd(all_fd_dict,verbose)
        
        ##产生test_bench
        if gene_tb:
            import testbench_generate as gt
            gt.generate_testbench(m_list[0],len(all_fd_dict),os.getcwd())
        
    ##文件夹测试
    elif sys.argv[1]=='-many':
        parent_dir=os.getcwd()
        input_file_dir=parent_dir+"\\test_input_netlist\\bench_virtex7" 
        print parent_dir
        print input_file_dir 
        cellref_set=set()
        cellref_set.update()
        for eachFile in os.listdir(input_file_dir):
            print eachFile
            if os.path.splitext(eachFile)[1] in ['.v','.vm']:
                input_file=os.path.join(input_file_dir,eachFile)    
                info=vm_parse(input_file)
                signal_list=info['signal_decl_list']
                m_list=info['m_list']
                cellref_list=mark_the_circut(m_list,allow_dsp=True,allow_unkown=False,verbose=False)
                cellref_set=cellref_set|set(cellref_list)
        for eachCellref in cellref_set:
            print eachCellref



