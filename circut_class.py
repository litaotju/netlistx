# -*- coding: utf-8 -*-
debug=False
import re

class port:
    '--this is a class of port in verilog--'
    def __init__(self,port_name,port_type,port_assign,port_width=1):
        self.port_name  =port_name
        self.port_type  =port_type   #input or output
        assert isinstance(port_assign,(signal,joint_signal)),\
            ("Error: add non-signal obj to port:%s"%self.port_name)
        self.port_assign=port_assign #assign_signal
        self.port_width =port_assign.width #每一个signal类型的变量会自动的计算出宽度
        
    def edit_port_assign(self,new_assign):
        assert isinstance(new_assign,(signal,joint_signal)),\
            ("Error: non-signal obj assgin to port %s"%self.port_name)
        self.port_assign=new_assign
        
    def __print__(self,is_top_port=False,pipo_decl=False):
        ##不同的端口有不同的打印方式,顶层模块()内的打印,pipo声明处的打印,以及primitive()的打印
        if is_top_port:
            print self.port_name,
        elif pipo_decl:
            if self.port_assign.vector==None:
                print self.port_type+" "+self.port_name+";"
            else:
                print self.port_type+" "+self.port_assign.vector+" "+self.port_name+";"
        else :
            assert isinstance(self.port_assign,(signal,joint_signal))
            print "    .%s("% self.port_name,
            self.port_assign.__print__()
            print ")",
            
class circut_module:
    '--this is a class of circut module in verilog--'
    def __init__(self,name='default',m_type='default',cellref='--top--',been_searched=False):
        self.name     =name
        self.m_type   =m_type
        self.cellref  =cellref
        self.been_searched=been_searched
        self.port_list =None
        self.param_list=None
        if debug:
            print 'create a %s instance:%s' %(self.cellref,self.name)
    ##featured 7.1
    def add_port_list(self,port_list):
        self.port_list=port_list
        port_assign_list=[]
        for eachPort in self.port_list:
            assert isinstance(eachPort,port),\
                ("Error: add non-port obj to port_list in module %s"%self.name)
            if isinstance(eachPort.port_assign,signal):
                port_assign_list.append(eachPort.port_assign.string)
            else:
                port_assign_list.append("__JOINT_SIGNAL__")
        self.port_assign_list=port_assign_list
        
    def add_param_list(self,param_list):
        self.param_list=param_list
        for eachParam in self.param_list:
            assert isinstance(eachParam,defparam),\
                ("Error: add non-defparam obj to param_list in module %s"%self.name)
    ##featured 7.1
                
    def add_port_to_module(self,port_name,port_type,port_assign,port_width):
        self.port_list.append(port(port_name,port_type,port_assign,port_width))
        
    def edit_spec_port(self,name,new_assign):
        edit_flag=False
        for current_port in self.port_list:
            if(current_port.port_name==name):
                current_port.edit_port_assign(new_assign)
                edit_flag=True
            else:
                continue
        assert edit_flag,("There is no port: %s in  %s %s."%(name,self.cellref,self.name))
        return edit_flag
        
    def print_module(self):
        '--不同的模块,默认的打印方式不同,顶层模块打印时,端口没有.name(assign)--'
        print self.cellref+"  "+self.name+"("
        assert(not self.port_list==None)
        #顶层模块的端口打印
        if self.m_type=='top_module':
#            pass
            for eachPort in self.port_list:
                assert isinstance(eachPort,port),eachPort.name
                eachPort.__print__(is_top_port=True)
                if not self.port_list.index(eachPort)==len(self.port_list)-1:
                    print ","
        #primitive的端口打印
        else:
            for eachPort in self.port_list:
                eachPort.__print__()
                if not self.port_list.index(eachPort)==len(self.port_list)-1:
                    print ","
        print "\n);"
        if not self.param_list==None:
            for eachParam in self.param_list:
                eachParam.__print__()
        return True
    def __print__(self):
        self.print_module()
###----------------------------------------------------------------------------
#featured 7.1

class signal:
    '--wire decled, primitive port_assignment--'
    def __init__(self,s_type='wire',name=None,vector=None):
        self.s_type=s_type
        self.name  =name
        self.vector=vector #如果非空,就是字符串类型的[nm1:num2]或者[num]
        self.width =1
        if vector==None:
            self.string=name
        else:
            self.string=name+vector;
        if not self.vector==None:
            self.get_width()
    def get_width(self):
        vector_match=re.match('\[(\d+):(\d+)\]',self.vector)
        bit_match=re.match('\[(\d+)\]',self.vector)
        if vector_match is not None:
            l=int(vector_match.groups()[0])
            r=int(vector_match.groups()[1])
            assert l>=r
            self.width=l-r+1
        else:
            assert (bit_match is not None)
            self.width=1
    
    def signal_2_port(self):
        '--将signal转换成port类型,主要在input output声明部分的信号--'
        assert (self.s_type in ['input','output','inout'])
        p1=port(self.name,self.s_type,self,self.width)
        return p1
    def __print__(self,is_wire_decl=False):
        #在{}中与在{}外的打印方式不同。
        #在{}中时,打印不要wire,input等关键字
        if not is_wire_decl:
            if self.vector==None: 
                print self.name,
            else: 
                print self.name+self.vector,
        #在{}外,也就是信号声明部分,打印是需要加关键字的
        else:
            if self.vector==None:
                print self.s_type+" "+self.name+" ;"
            else:
                print self.s_type+" "+self.vector+" "+self.name+";"
class joint_signal:
    '--this is a special signal type for signal concut in { }--'
    def __init__(self):
        self.sub_signal_list=[]
        self.width=0
    def joint_one_more(self,new_signal):
        assert isinstance(new_signal,signal),"%s is not a signal obj"%str(new_signal)
        self.sub_signal_list.append(new_signal)
        self.width+=new_signal.width
    def __print__(self):
        print "{",
        for eachSignal in self.sub_signal_list:
            eachSignal.__print__()
            if not (self.sub_signal_list.index(eachSignal)\
                ==len(self.sub_signal_list)-1):
                print ",",
        print "}",

class defparam:
    '--this is a class for defparam statement--'
    def __init__(self,name,attr,value):
        self.name=name
        self.attr=attr
        self.value=value
    def edit_param(self,attr,new_value):
        assert self.attr==attr
        self.value=new_value
    def __print__(self):
        if type(self.value)=='str':
            value_str=self.value
        else:
            value_str=str(self.value)
        print "defparam %s .%s=%s ;"%(self.name,self.attr,value_str)
class assign:
    '--this is a class of assign statement--'
    def __init__(self,kwd="assign",left_signal=None,right_signal=None):
        self.kwd=kwd        
        self.left_signal =left_signal
        self.right_signal=right_signal        
    def __print__(self):
        print self.kwd+" ",
        self.left_signal.__print__()
        print " = ",
        self.right_signal.__print__()
        print " ;"
