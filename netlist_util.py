'--this file is composed of a lot of functions to parse and util the Src file--'
import os
import re
import circut_class
import generate_testbench as gt
###############################################################################   
def remove_comment(fname,write_file=False):
    '--remove comment has begining of // and return strings to a list eachLine--'
    try:
        fobj=open(fname,'r')
        if write_file:
            fobj_copy=open(fname[:-3]+'_no_comment.v','w')
    except IOError,e:
        print "Error: file open error:",e        
    else:
        all=[]
        for eachLine in fobj:
            if re.match('^\s*//',eachLine) is not None:
                continue
            else:
                all.append(eachLine)
        if write_file:
            fobj_copy.writelines([x for x in all ])
            fobj_copy.close()
        fobj.close()
        print 'Note: remove_comment() successfully'
        return all

###############################################################################    
def extract_m_list(fname,verbose=False):
    '--extract the module list from a verilog src--'
    fobj=open(fname,'r')
    
    #to parent function
    signal_list=[]
    module_list=[]
    defparam_init_list={}

    #local variable
    temp_module=[]
    ##---------------------------------------------------
    for eachLine in fobj:
        if re.match('[^;]*;$',eachLine) is not None:
            temp_module.append(eachLine)                      
            for eachStm in temp_module:
                ##match the top ports of top module and add to module_object 
                top_port_match=re.match('\s*(input|output)\s+\[([0-9]+)\:([0-9]+)\]\s+(\w+)',eachStm) 
                top_port_match2=re.match('\s*(input|output)\s+(\w+)',eachStm) 
                if top_port_match is not None: 
                    assert module_list[0].cellref=="module","module_list[0] is not top module"
                    port_type =top_port_match.groups()[0]
                    port_name =top_port_match.groups()[3]
                    port_width=int(top_port_match.groups()[1])-int(top_port_match.groups()[2])+1
                    module_list[0].add_port_to_module(port_name,port_type,port_name,port_width)
                elif top_port_match2 is not None:
                    assert module_list[0].cellref=="module","module_list[0] is not top module"
                    port_type =top_port_match2.groups()[0]
                    port_name =top_port_match2.groups()[1]
                    module_list[0].add_port_to_module(port_name,port_type,port_name,1)
                ##match the middle signal
                elif re.match('\s*wire\s+.',eachStm) is not None:
                    signal_list.append(eachStm)
                ##macth the primitive instances
                else:
                    #if the last one chacracter is (,this a stm of a module delcaration
                    m_decl_stm  =re.match('\s*(\w+)\s+([^\s]+)\s+\($',eachStm)
                    port_decl   =re.match('\s*\.(\w+)\((.+)\)\,?',eachStm)
                    defparam_stm=re.match('\s*(defparam)\s+([^\s]+)(.INIT=)([1-9]+\'h[0-9A-F]+)\;',eachStm)
                    if m_decl_stm     is not None:
                        cellref=m_decl_stm.groups()[0]
                        name   =m_decl_stm.groups()[1]
                        if m_decl_stm.groups()[0]=='module':
                            m_type='top_module'
                        else:
                            m_type='un_init'
                        module=circut_class.circut_module(name,m_type,cellref)
                    elif port_decl    is not None:
                        port_name=port_decl.groups()[0]
                        port_assign=port_decl.groups()[1]
                        port_type='notknown'
                        module.add_port_to_module(port_name,port_type,port_assign,1)
                    elif defparam_stm is not None:
                        init_obj_name=defparam_stm.groups()[1]
                        init_value   =defparam_stm.groups()[3]
                        defparam_init_list[init_obj_name]=init_value
            if module is not None:
                module_list.append(module)
            module=None
            temp_module=[]
        else:
            temp_module.append(eachLine)

    ##---------------------------------------------------
    assert module_list[0].cellref=="module","Error: m_list[0] is not top module"
    fobj.close()
    mark_the_circut(module_list,verbose)
    if verbose:
        print "Info: Top module is :"+module_list[0].name
    print 'Note: extact_m list() successfully !'
    return signal_list,module_list,defparam_init_list

###############################################################################
def print_module_list(module_list):
    for eachModule in module_list:
        print eachModule.cellref,eachModule.name,eachModule.m_type
        for eachPort in eachModule.port_list:
            print str(eachPort.port_width)+'.'+eachPort.port_name+'('+eachPort.port_assign+')'
    print 'Note:Print module_list done!'
    return True

###############################################################################
def mark_the_circut(m_list,verbose=False):
    
    #mark all the module with a type
    for eachModule in m_list[1:]:
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
            if re.match('L?O',eachModule.port_list[-1].port_name) is None:
                print 'Error '+eachModule.cellref+'  '+eachModule.name
                print '      info:This lut\'s last PORT is NOT LO'
                return False
            for eachPort in eachModule.port_list[:-1]:
                eachPort.port_type='input'
            eachModule.port_list[-1].port_type='output'

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
                if eachPort.port_name=='I':
                    eachPort.port_type='input'
                elif eachPort.port_name=='O':
                    eachPort.port_type='output'
                else:
                    print 'Error: in netlist_util.mark_the_circut()'
                    print '       buf %s has a port is neither I nor O' % eachModule.name
        #GND VCC---------------------------------------------------------------
        elif (eachModule.cellref=='GND' or eachModule.cellref=='VCC'):
            eachModule.m_type=eachModule.name
            for eachPort in eachModule.port_list:
                eachPort.port_type='output'
        #DSP48E---------------------------------------------------------------
        elif re.match('DSP48|DSP48E\w*',eachModule.cellref) is not None:
            eachModule.m_type='DSP'
        else:
            print 'Warning:unknown cellref:'+eachModule.cellref+eachModule.name
    print "Note: mark_the_circut() successfully !"
    if verbose:        
        print 'Note:module list is:'
        print_module_list(m_list)
    return True

###############################################################################
def get_all_fd(m_list,verbose=False):
    '--get all the FD and its D_Q port--'
    all_fd_dict={}    
    if verbose:
        print '-----------------------------------------'
        print 'Note:all the FD and its D port assign Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='FD':
            for eachPort in eachModule.port_list:
                if eachPort.port_name=='D':
                    for eachPort_Q in eachModule.port_list:
                        if eachPort_Q.port_name=='Q':
                            all_fd_dict[eachModule.name]=[eachPort.port_assign,eachPort_Q.port_assign]
                            if verbose:
                                print 'D:%s--FD:>>%s-->>Q:%s' \
                                %(eachPort.port_assign,eachModule.name,eachPort_Q.port_assign)
    print "Note: get_all_fd() sucessfully !"
    return all_fd_dict
###############################################################################
def get_all_lut(m_list,verbose=False):
    all_lut_dict={}
    all_lut_cnt=[0,0,0,0,0,0]
    if verbose:
        print '-----------------------------------------'
        print 'Info: all the LUT and its name Are:'
    for eachModule in m_list[1:]:
        if eachModule.m_type=='LUT':
            all_lut_dict[eachModule.name]=eachModule.cellref    
            lut_kind=int(eachModule.cellref[3])-1
            all_lut_cnt[lut_kind]=all_lut_cnt[lut_kind]+1       
    return all_lut_dict,all_lut_cnt
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
            if eachModule.m_type=='LUT' and eachModule.been_searched==False \
            and eachModule.port_list[-1].port_assign==all_fd_dict[each_FD][0]:
                if int(eachModule.cellref[3])<=(K-2):
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
def get_all_clock(m_list,all_fd_list,verbose):
    clock_list=[]
    for eachModule in m_list[1:]:
        if eachModule.name in all_fd_list:
            for eachPort in eachModule.port_list:
                if eachPort.port_type=="clock":
                    if eachPort.port_assign not in clock_list:
                        clock_list.append(eachPort.port_assign)
                    else:
                        continue
    assert len(clock_list)==1,\
    "Warning: this circut has more than 1 clock domain.clock cnt is %d" %len(clock_list)
    if verbose:
        print "Info:all clock signals are as follows:"
        for clock in  clock_list:
            print clock
    print "Note: get_all_clock() successfully !"
    return clock_list
    
###############################################################################
def get_ce_in_fd(m_list,all_fd_list,verbose):
    ce_signal_list=[]
    fd_has_ce_list=[]
    for eachModule in m_list[1:]:
        if eachModule.name in all_fd_list:
            for eachPort in eachModule.port_list:
                if eachPort.port_name=='CE':
                    fd_has_ce_list.append(eachModule.name)
                    if eachPort.port_assign not in ce_signal_list:
                        ce_signal_list.append(eachPort.port_assign)
                else:
                    continue
    if verbose:
        print "Note:all ce signal are as follows:"
        for ce in ce_signal_list:    
            print ce
    print"Note: get_ce_in_fd() successfully !"
    return ce_signal_list,len(fd_has_ce_list),fd_has_ce_list
###############################################################################  
if __name__=='__main__':
    print "Current PATH is:"+os.getcwd()
    print [file for file in os.listdir(os.getcwd())]    
    fname=raw_input('plz enter the file name:') 
    K=int(raw_input('plz enter the K parameter of FPGA:K='))
    signal_list,m_list,defparam_list=extract_m_list(fname,True)
    all_fd_dict=get_all_fd(m_list,False)
    lut_out2_FD_dict,FD_din_lut_list=get_lut_cnt2_FD(m_list,all_fd_dict,True,K)
    ce_signal_list=get_ce_in_fd(m_list,all_fd_dict.keys(),False)
    clock_signal_list=get_all_clock(m_list,all_fd_dict,verbose=True)
    gt.generate_testbench(m_list[0],len(all_fd_dict),os.getcwd())



                

