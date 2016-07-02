# -*- coding: utf-8 -*-

import re

class port(object):
    u'''
        代表verilog 网表中的 port的类
    '''
    PORT_TYPE_CLOCK = 'clock'
    PORT_TYPE_INPUT = 'input'
    PORT_TYPE_INOUT = 'inout'
    PORT_TYPE_OUTPUT = 'output'
    PORT_TYPE_UNKOWN = 'unkown'
    ALLOWED_TYPES = (PORT_TYPE_CLOCK, PORT_TYPE_INPUT, PORT_TYPE_INOUT,
                     PORT_TYPE_OUTPUT, PORT_TYPE_UNKOWN)

    def __init__(self, port_name, port_type, port_assign, port_width=1):
        u'''
            @brief:
            @params:
                port_name, any str
                port_type, one of the port.ALLOWED_TYPES
                port_assign, an instance of signal or joint_sigal
                port_width, an int, default is 1
        '''
        self.port_name = port_name
        self.port_type = port_type
        self.port_assign = port_assign
        self.port_width = port_assign.width #每一个signal类型的变量会自动的计算出宽度

    def edit_port_assign(self,new_assign):
        self.port_assign = new_assign

    def split(self):
        u'''将一个多bit的端口自动的分解为单bit的端口，用于图的建模，便于将PIPO分解
           @return：一个队列，含有拆分后的一个或多个port类对象
        '''
        if self.port_assign.vector == None:
            return [self]
        ports = []
        lsb, msb = self.port_assign.lsb, self.port_assign.msb 
        loop = range(lsb, msb+1) if lsb <= msb else range(msb, lsb+1) 
        for i in loop:
            subassign = signal(self.port_type, self.name, "[%d]"% i)
            subport = port(self.name, self.port_type, subassign )
            ports.append(subport)
        return ports

    def __print__(self, is_top_port=False, pipo_decl=False):
        u'''不同的端口有不同的打印方式,顶层模块()内的打印,pipo声明处的打印,以及primitive()的打印
        '''
        if is_top_port:
            print self.port_name,
        elif pipo_decl:
            if self.port_assign.vector == None:
                print self.port_type + " " + self.port_name + ";"
            else:
                print self.port_type + " " + self.port_assign.vector + " " + self.port_name + ";"
        else :
            print "    .%s("% self.port_name,
            self.port_assign.__print__()
            print ")",

    def __str__(self):
        u'''只供调试使用，在最终输出的Verilog网表中不应该使用这样的语句来打印端口
        '''
        return "%s %s %s %s\n" %\
            (self.port_type, self.port_name, self.port_assign.string, self.port_width)

    @property
    def port_type(self):
        if self.__port_type == port.PORT_TYPE_UNKOWN:
            print "Warning: the port %s 's port_type is port.PORT_TYPE_UNKOWN" % self.port_name
        return self.__port_type

    @port_type.setter
    def port_type(self, value):
        if value not in port.ALLOWED_TYPES:
            raise ValueError, 'port_type must be in %s, but here is %s' \
                % ( port.ALLOWED_TYPES, value)
        self.__port_type = value

    @property
    def port_assign(self):
        return self.__port_assign

    @port_assign.setter
    def port_assign(self, value):
        assert isinstance(value, (signal,joint_signal)), \
            ("Error: add non-signal obj to port:%s" % self.port_name)
        self.__port_assign = value

    @property
    def name(self):
        u"name只有只读属性"
        return self.port_name

class circut_module:

    def __init__(self,name='default',m_type='default',cellref='--top--',been_searched=False):
        self.name     =name
        self.m_type   =m_type
        self.cellref  =cellref
        self.been_searched=been_searched
        self.port_list =None
        self.param_list=None
        debug=False
        if debug:
            print 'create a %s instance:%s' %(self.cellref,self.name)

    def add_port_list(self,port_list):
        self.port_list=port_list
        port_assign_list=[]
        for eachPort in self.port_list:
            assert isinstance(eachPort,port),\
                ("Error: add non-port obj to port_list in module %s"%self.name)
            if isinstance(eachPort.port_assign,signal):
                port_assign_list.append(eachPort.port_assign.string)
            else:
                assert isinstance(eachPort.port_assign,joint_signal)
                for eachSubsignal in eachPort.port_assign.sub_signal_list:
                    port_assign_list.append(eachSubsignal.string)
        self.port_assign_list=port_assign_list
        
    def add_param_list(self,param_list):
        self.param_list=param_list
        for eachParam in self.param_list:
            assert isinstance(eachParam,defparam),\
                ("Error: add non-defparam obj to param_list in module %s"%self.name)
                
    def add_port_to_module(self,port_name,port_type,port_assign,port_width):
        self.port_list.append(port(port_name,port_type,port_assign,port_width))
        
    def edit_spec_port(self,name,new_assign):
        edit_flag=False
        for current_port in self.port_list:
            if(current_port.port_name==name):
                current_port.edit_port_assign(new_assign)
                edit_flag=True
                break
            else:
                continue
        assert edit_flag,("There is no port: %s in  %s %s."%(name,self.cellref,self.name))
        return None
        
    def print_module(self):
        '--不同的模块,默认的打印方式不同,顶层模块打印时,端口没有.name(assign)--'
        print self.cellref+"  "+self.name+" ("
        assert(not self.port_list==None)
        #顶层模块的端口打印
        if self.m_type=='top_module':
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
        if self.param_list!=None:
            for eachParam in self.param_list:
                eachParam.__print__()
        return True

    def __print__(self):
        self.print_module()
    
    def __str__(self):
        ports = [(port.port_name, port.port_assign.string) for port in self.port_list ]
        portlist = ""
        if self.cellref == "module":
            for name, assign in ports:
                portlist += "%s ,\n" % name
        else:
            for name, assign in ports:
                portlist += "    .%s( %s ),\n" % (name, assign)
        portlist = portlist[:-2]
        paramlist = ""
        if self.param_list != None:
            for para in self.param_list:
                paramlist +=  "defparam %s .%s=%s ;\n" %\
                             (para.name,para.attr,str(para.value) )
        return "%s %s (\n%s\n);\n%s" % (self.cellref , self.name , portlist , paramlist)

    def input_count(self):
        return len([p for p in self.port_list if p.port_type =="input" ])


class signal:

    def __init__(self, s_type='wire', name=None, vector=None):
        '''@param: s_type = ['wire', 'input','output','inout']
                   name = id_string,
                    vector = [\d+:\d+]
        '''
        self.s_type = s_type
        self.name  = name
        self.vector = vector #None,or string 类型的[nm1:num2]或者[num]
        self.width = 1
        self.lsb = 0
        self.msb = 0
        self.bit_loc = 0
        if vector == None:
            self.string = name
        else:
            self.string = name + vector
            self.__get_width()

    def __get_width(self):
        vector_match = re.match('\[(\d+):(\d+)\]',self.vector)
        bit_match = re.match('\[(\d+)\]',self.vector)
        if vector_match is not None:
            l = int(vector_match.groups()[0])
            r = int(vector_match.groups()[1])
            #assert l>=r
            if l >= r:
                self.width = l - r + 1
            else:
                self.width = r - l + 1
            ##featured 7.2,将信号的高位与低位两个数字存下来,之后在判断Prim端口是否向连接,有作用
            self.lsb = l
            self.msb = r
        else:
            assert (bit_match is not None)
            self.bit_loc=int(bit_match.groups()[0])
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
                print self.s_type+" "+self.vector+" "+self.name+" ;"
                
    def __eq__(self, obj):
         ## 比较两个signal 对象是否相等，直接比较name, s_type和vector三个字符串
         ## 属性是否相等，相等则断言其他根据这几个属性推出的属性也必然相等
         assert isinstance(obj, signal),"%s" % str(obj.__class__)
         if self.name != obj.name:
             return False
         if self.s_type != obj.s_type:
             return False
         if self.vector != obj.vector:
             return False
         assert self.bit_loc == obj.bit_loc
         assert self.lsb == obj.lsb
         assert self.msb == obj.msb
         assert self.width == self.width
         return True


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
    def __init__(self, kwd="assign", left_signal=None, right_signal=None):
        self.kwd = kwd
        assert isinstance(left_signal, signal) and isinstance(right_signal, signal)
        self.left_signal = left_signal
        self.right_signal = right_signal
        self.name = left_signal.string
          
    def __print__(self):
        print self.kwd+" ",
        if isinstance(self.left_signal,signal):
            self.left_signal.__print__()
        else:
            assert type(self.left_signal)==str
            print self.left_signal,
        print " = ",
        if isinstance(self.right_signal,signal):
            self.right_signal.__print__()
        else:
            assert type(self.right_signal)==str,"%s,type %s "%(self.right_signal,type(self.right_signal))
            print self.right_signal,
        print " ;"
    
    def __str__(self):
        "assign语句一定是以等号连接的"
        left = self.left_signal
        right = self.right_signal
        return "%s %s = %s ;" % (self.kwd, left.string, right.string)

isDff  = lambda obj: isinstance( obj, circut_module) and obj.m_type == "FD"
isComb = lambda obj: isinstance( obj, circut_module ) and obj.m_type != "FD"
isLUT = lambda obj: isinstance(obj, circut_module) and obj.m_type=="LUT"
isPort = lambda obj: isinstance( obj, port)

class Port(port):
    pass

class CircuitModule(circut_module):
    pass

class Signal(signal):
    pass

class JointSignal(joint_signal):
    pass

class Defparam(defparam):
    pass

class Assign(assign):
    pass

###featured 7.3--------------------------------------------------------------
###
#class vertex:
#    def __init__(self,obj):
#        if isinstance(obj,port):
#            self.entity=obj
#            self.type =obj.port_type
#        else:
#            assert isinstance(obj,circut_module)
#            self.entity=obj
#            self.type  =obj.cellref
#        self.label=self.type+"  "+self.obj.name
#class edge:
#    def __init__(self,s,d):
#        pass
###featured 7.3--------------------------------------------------------------
#prim_dict={
#    "LUT6_2":{'I':['I0','I1','I2','I3','I4','I5'],'O':['O5','O6']},
#    "XORCY":{'I':['LI','CI'],'O':['O']},
#    "MULT_AND":{'I':['I0','I1'],'O':['LO']},
#    "MUXCY_L":{'I':['DI','CI','S'],'O':['LO']},
#    "MUXCY":{'I':['DI','CI','S'],'O':['O']},
#    "MUXF5":{'I':['I0','I1','S'],'O':['O']},
#    "MUXF6":{'I':['I0','I1','S'],'O':['O']},
#    "MUXF7":{'I':['I0','I1','S'],'O':['O']},
#    "MUXF8":{'I':['I0','I1','S'],'O':['O']},
#    "INV"  :{'I':['I'],'O':['O']}, 
#    "GND":{'O':['G']},
#    "VCC":{'O':['P']}
#    }  

#if __name__ == "__main__":
#    x = signal('wire', 'x', '[10:10]')
#    y = signal('wire', 'x', '[10:10]')
#    assert x == y
#    print x == y
#    assert not ( x is y)      