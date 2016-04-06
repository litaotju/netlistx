# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 21:13:37 2015

@author: litao
"""
import re
import sys
import os

import netlistx.circuit as cc

import netlist_lexer
import yacc

tokens=netlist_lexer.tokens

###############################################################################
def p_vmfile(p):
    '''vm_file : module_decl port_decl_list signal_decl_list primitive_list assign_stm_list ENDMODULE
               | module_decl port_decl_list signal_decl_list primitive_list ENDMODULE
    '''
    #将所有的部分都存到序列p[0]当中
    p[1].add_port_list(p[2]) #将port_decl_list返回的端口给top_module加上
    p[0]={}
    m_list=[]
    m_list.append(p[1])
    m_list+=p[4]
    p[0]['m_list']=m_list
    p[0]['port_decl_list']  =p[2]
    p[0]['signal_decl_list']=p[3]
    p[0]['primitive_list']  =p[4]
    if len(p)==7:
        p[0]['assign_stm_list']=p[5]
    else:
        p[0]['assign_stm_list']= []
#---------------------------------------------------------------------
#----顶层模块声明区
#---------------------------------------------------------------------    
def p_module_decl(p):
    '''module_decl : MODULE IDENTIFIER '(' pipo_list ')' ';'
    '''
    p[0]=cc.circut_module(name=p[2],m_type='top_module',cellref='module')
    
def p_pipo_list(p):
    '''pipo_list : pipo_list IDENTIFIER
                 | IDENTIFIER
    '''
    pass
#---------------------------------------------------------------------
#----端口和信号声明区
#---------------------------------------------------------------------        
def p_port_decl_list(p):
    '''port_decl_list : port_decl_list port_decl
                     | port_decl
    '''
    if len(p)==3:
        p[1].append(p[2])
        p[0]=p[1]
    else:
        p[0]=[]
        p[0].append(p[1])	
        
def p_port_decl(p):
    '''port_decl     : INPUT  IDENTIFIER ';'
                     | INPUT  VECTOR IDENTIFIER ';'
                     | OUTPUT IDENTIFIER ';'
                     | OUTPUT VECTOR IDENTIFIER ';'
                     | INOUT  IDENTIFIER ';'
                     | INOUT  VECTOR IDENTIFIER ';'
    '''
    if len(p)==5:
        tmp=cc.signal(s_type=p[1],name=p[3],vector=p[2])
        p[0]=tmp.signal_2_port()

    else:
        tmp=cc.signal(s_type=p[1],name=p[2],vector=None)    
        p[0]=tmp.signal_2_port()

def p_signal_decl_list(p):
    '''signal_decl_list : signal_decl_list signal_decl
                        | signal_decl
    '''
    if len(p)==3:
        p[1].append(p[2])
        p[0]=p[1]
    else:
        p[0]=[]
        p[0].append(p[1])
        
def p_signal_decl(p):
    ''' signal_decl    : WIRE VECTOR IDENTIFIER ';'
                       | WIRE IDENTIFIER ';'
    '''
    if len(p)==5:
        p[0]=cc.signal(name=p[3],vector=p[2])
    else:
        p[0]=cc.signal(name=p[2],vector=None)
#---------------------------------------------------------------------
#----primitive区
#---------------------------------------------------------------------   
def p_primitive_list(p):
    '''primitive_list : primitive_list primitive
                      | primitive
    '''
    if len(p)==3:
        p[1].append(p[2])
        p[0]=p[1]
    else:
        p[0]=[]
        p[0].append(p[1])
def p_primitive(p):
    '''primitive      : IDENTIFIER IDENTIFIER     '(' primitive_port_list ')' ';'
                      | IDENTIFIER IDENTIFIER BIT '(' primitive_port_list ')' ';' 
                      | IDENTIFIER IDENTIFIER     '(' primitive_port_list ')' ';'    defparam_list
                      | IDENTIFIER IDENTIFIER BIT    '(' primitive_port_list ')' ';' defparam_list
                      | IDENTIFIER IDENTIFIER VECTOR '(' primitive_port_list ')' ';' defparam_list
    '''
    if len(p)==7:
        p[0]=cc.circut_module(name=p[2],cellref=p[1])
        p[0].add_port_list(p[4])
    elif len(p)==8:
        if not p[3]=='(': #WITH BIT and NO para
            p[0]=cc.circut_module(name=p[2]+p[3],cellref=p[1])
            p[0].add_port_list(p[5])
        else: #NO BIT ,WITH PARA
            p[0]=cc.circut_module(name=p[2],cellref=p[1])
            p[0].add_port_list(p[4])
            p[0].add_param_list(p[7])
    elif len(p)==9:
        p[0]=cc.circut_module(name=p[2]+p[3],cellref=p[1])
        p[0].add_port_list(p[5])
        p[0].add_param_list(p[8])
def p_primitive_port_list(p):
    '''primitive_port_list : primitive_port_list primitive_port
                           | primitive_port
    '''
    if len(p)==3:
        p[1].append(p[2])
        p[0]=p[1]
    else:
        p[0]=[]
        p[0].append(p[1])
def p_primitive_port(p):
    '''primitive_port : '.' IDENTIFIER '('     signal_element ')' 
                      | '.' IDENTIFIER '(' '{' joint_signal_list '}' ')'
    '''
    if len(p)==6:#signal_element
        p[0]=cc.port(port_name=p[2],port_type='un_known',port_assign=p[4])
    else:#joint_signal_list
        p[0]=cc.port(p[2],'un_known',p[5])
    #the port_type of unkown you just handle it in the mark_the_circuit func
def p_joint_signal(p):
    '''joint_signal_list  : joint_signal_list signal_element
                          | signal_element
    '''
    if len(p)==3:
        p[1].joint_one_more(p[2])
        p[0]=p[1]
    else:
        p[0]=cc.joint_signal()
        p[0].joint_one_more(p[1])
def p_signal_element(p):
    '''signal_element : IDENTIFIER BIT
                      | IDENTIFIER VECTOR
                      | IDENTIFIER
    '''
    if len(p)==3:
        p[0]=cc.signal(name=p[1],vector=p[2])
    else:
        # 匹配，使得连在一起的 ID-VEC：ID[\d+]等够将ID VEC分开
        linked_id_vec = re.match("(.+)(\[\d+\])$",p[1])
        if linked_id_vec is not None:
            iden = linked_id_vec.groups()[0]
            vec = linked_id_vec.groups()[1]
            p[0] = cc.signal( name = iden ,vector = vec)
        else:
            p[0]=cc.signal(name=p[1])
def p_defparam_list(p):
    '''defparam_list  : defparam_list defparam_stm
                      | defparam_stm
    '''
    if len(p)==3:
        p[1].append(p[2])
        p[0]=p[1]
    else:
        p[0]=[]
        p[0].append(p[1])
def p_defparam_(p):
    '''defparam_stm   : DEFPARAM IDENTIFIER                 '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER        '.' INIT '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER BIT    '.' INIT '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER VECTOR '.' INIT '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER VECTOR '.' IDENTIFIER '=' NUMBER ';'
                      | DEFPARAM IDENTIFIER VECTOR '.' IDENTIFIER '=' '"' STRING_CON '"' ';'
    '''
    if len(p)==6:
        splited=p[2].split(".")
        assert splited[-1]=="INIT"
        entity_name=p[2][:-5]
        p[0]=cc.defparam(entity_name,"INIT",p[4])
    elif len(p)==8:
        p[0]=cc.defparam(p[2],p[4],p[6])
    elif len(p)==9:
        p[0]=cc.defparam(p[2]+p[3],p[5],p[7])
    else:#string_con
        p[0]=cc.defparam(p[2]+p[3],p[5],p[7]+p[8]+p[9])
#---------------------------------------------------------------------
#----assign区
#--------------------------------------------------------------------- 
def p_assign_stm_list(p):
    '''assign_stm_list  : assign_stm_list assign_stm
                        | assign_stm
    '''
    if len(p)==3:
        p[1].append(p[2])
        p[0]=p[1]
    else:
        p[0]=[]
        p[0].append(p[1])
def p_assign_stm(p):
    ''' assign_stm      : ASSIGN signal_element '=' signal_element ';'
                        | ASSIGN signal_element '=' BIN_NUMBER ';'    
    '''
    if isinstance(p[4],cc.signal):
        p[0]=cc.assign("assign",p[2],p[4])
    else:
        p[0]=cc.assign("assign",p[2],cc.signal(name=p[4]))
def p_error(p):
    if p:
         print "Syntax error at token %s :%s in line %d " % ( p.type , p.value,p.lexer.lineno)
         exit(0)            
    else:
         print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc()

###############################################################################
def vm_parse(input_file):
    '''returns info of input vm file as a list,
        info['m_list'][0]        is a instance of cc.circut_module which is top_module in vm,
        info['port_decl_list']   is the input_ouput decl list of vm file,
        info['signal_decl_list'] is the wire        decl list,
        info['m_list'][1:]       is the primitive instances(cc.circut_module obj) list,and the defparam of primitive(if exist)
        info['assign_stm_list']  is the assign list of a file 
    '''
    try:
        fobj=open(input_file,'r')
    except IOError,e:
        print "Error: file open error:",e
        raise SystemExit
    else:
        all_lines=fobj.read()
        fobj.close()
        p=parser.parse(all_lines)
        #--------------------------------
        #打印部分
        #--------------------------------
        if __name__ == "__main__":
            output_file=os.path.splitext(input_file)[0]+"_rewrite.v"
            fobj2 = open(output_file,'w')
            console=sys.stdout
            sys.stdout=fobj2
            p['m_list'][0].__print__() #top-module
            for eachPort_decl in p['port_decl_list']:
                eachPort_decl.__print__(pipo_decl=True)
            for eachSignal in p['signal_decl_list']:
                eachSignal.__print__(is_wire_decl=True)
            for eachPrimitive in p['m_list'][1:]:
                eachPrimitive.__print__()
            if len(p)==5:
                for eachAssign in p['assign_stm_list']:
                    eachAssign.__print__()
            print "endmodule;"
            sys.stdout=console
            fobj2.close()
        #------------------------------------
        #解析完完全打印出来
        #------------------------------------
        parser.restart()
        print "Job: parse the vm file %s finished."% input_file
        return p
    
###############################################################################

if __name__=='__main__':
    if len(sys.argv)==1:
        while(1):
            print "Just handle one simple verilog netlist in os.get_cwd() dir"
            fname=raw_input("plz enter the file name:")
            info=vm_parse(fname)
            m_list=info['m_list']
            if m_list:
                print "Parse %s successfully " % fname
                print "Info: find %d primitive in %s "% (len(m_list)-1,fname)


