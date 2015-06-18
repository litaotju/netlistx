# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 16:30:03 2015

@author: litao
"""
import re
import circut_class
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