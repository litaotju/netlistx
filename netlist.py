# -*- coding:utf-8 -*- #
import os
import sys
import re

# user-defined module
from netlistx import vm_parse
from netlistx.exception import * 
import netlistx.netlist_util as nu
import netlistx.class_circuit as cc


class Netlist(object):
    ''' 
        数据属性：存储由解析器解析所得的整个网表的结构
        方法属性：查询，修改，插入，输出
        类的应用场合：确保网表在修改时候的完整性，
                     而不是只修改了m_list, 其余部分没有修改。
        关于scan_chain的应用：
            首先使用parser进行提取，然后使用netlist_util中的函数进行可以用资源信息的识别
            之后再调用netlist对象本身的成员函数进行网表的编辑。
    '''
    def __init__(self, vminfo):
        '''@param: vminfo, a dict returned from netlist_parser
            self.top_module  = vminfo['m_list'][0]
            self.ports       = vminfo['port_decl_list']        
            self.wires       = vminfo['signal_decl_list']
            self.primtives   = vminfo['primitive_list']
            self.assigns     = vminfo['assign_stm_list']
        '''
        print "Job: getting Netlist..."
        self.m_list = vminfo['m_list']
        # 根据解析器的信息存储
        self.top_module  = vminfo['m_list'][0]
        self.ports       = vminfo['port_decl_list']        
        self.wires       = vminfo['signal_decl_list']
        self.primitives  = vminfo['primitive_list']
        self.assigns     = vminfo['assign_stm_list']
    
        self.others = None
        # 建立一系列字典，提升查询的效率
        self._ports     = self.__build_dict(self.ports,    "name" )
        self._wires     = self.__build_dict(self.wires,    "name" )
        self._primitives = self.__build_dict(self.primitives, "name" )
        self._assigns   = self.__build_dict(self.assigns,   "name" )

        # 规定不同的类型的搜索函数
        self.search_callable = {'ports' : self.search_port ,
                   'wires' :    self.search_wire , 
                   'primitives':self.search_prim, 
                   'assigns':   self.search_assign
                   }
        self.cellrefs = nu.mark_the_circut( self.primitives, allow_unkown = False)
        print "Job: Netlist get. OK!\n"
        return None

    # 建立内部字典和查询内部字典的工厂方法
    def __build_dict(self, iterable, attr_as_key):
        '''@param : iterable, 是一个可迭代对象或者None
                    attr_as_key, 可迭代对象里面的元素的一个attr名称，使用getattr获取
           @return: tdict = {}, key: 可迭代对象里面的元素的attr值
                                val: 可迭代对象的元素本身
           @brief :将可迭代对象转换为一个 由特定的键值索引的字典。
        '''
        tdict = {}
        if iterable is None:
            return tdict
        for obj in iterable:
            key = getattr(obj, attr_as_key)
            if not tdict.has_key(key):
                tdict[ key ] = obj
            else:
                errmsg = "Error: Redecleration of %s obj : %s" \
                        % (obj.__class__ , key )
                raise RedeclarationError, errmsg
        return tdict

    def __search_dict(self, dict_name, target):
        '''@param: dict_name, self的一个字典数据属性
                   target, 一个ID
           @return: None或者dict_name中的一个值
        '''
        try:
            tdict = getattr(self, dict_name)
        except AttributeError:
            errmsg = "Error: netlist has no attr %s" % dict_name
            raise Exception, errmsg
        try:
            result = tdict[target]
        except KeyError:
            return None
        else:
            return result
    
    def __insert_type(self, itype, element, hashable_attr = "name"):
        '''@brief:
                私有工厂方法，向 itype类型的容器里面加入一个element, 并且将这个
                element的hashable_attr属性作为键值，进行索引，索引相同时
                raise一个 RedeclarationError的异常。默认的索引是name属性。
        '''
        assert hasattr(element, hashable_attr)
        key = getattr(element, hashable_attr)
        seq_container  = getattr(self, itype)
        dict_container = getattr(self, "_"+itype )
        has_one = self.search_callable[itype]( key )
        if has_one is not None:
            errmsg = "Error: redeclaration of %s %s" % (itype, key)
            raise RedeclarationError(errmsg)
        else:
            seq_container.append(element)
            dict_container[element.name] = element
            
    # 查询的方法组
    def get_top(self):
        return self.top_module
 
    def search_port(self, name):
        "@para: top module's port_name"
        return self.__search_dict("_ports", name )

    def search_wire(self, name):
        "@para: wire's name"
        return self.__search_dict("_wires", name)

    def search_prim(self, name):
        "@para: prim's name"
        return self.__search_dict("_primitives", name )
    
    def search_assign(self, name):
        "@para: assign's left name"
        return self.__search_dict("_assigns", name )

    # 插入的方法组
    def insert_prim(self, prim):
        '''@param: prim, a cc.circut_module 对象
           @return: 插入成功的prim对象
        '''
        assert isinstance(prim, cc.circut_module)
        self.__insert_type("primitives", prim)
        try:
            p_assigns = prim.port_assign_list
        except AttributeError:
            print "Warning: inserted prim has no ports and port_assigns "
        else:
            if len( p_assigns)==0:
                print "Warning: inserted prim with has no port_assigns"
            else:
                for signal in p_assigns:
                    self.insert_wire( signal )
        return prim

    def insert_wire(self, signal):
        '''@param: signal, 一个signal对象，
                    或者是一个可以转化为signal的字符串.空格分隔，长度为2个词，后一个是向量.或者单个词
           @return:如果成功插入则返回一个signal对象，如果失败，则返回None
        '''
        if isinstance(signal, cc.signal):
            s = signal
        elif isinstance(signal, str):
            ss = signal.split()
            if len(ss) == 2:
                assert re.match("\[\d+\]|\[\d+:\d+\]", ss[1])
                s = cc.signal(name = ss[0], vector = ss[1])
            else:
                s = cc.signal(name = ss[0])
        else:
            raise FormatError,"param type error: not a signal or a string."
        try:
            self.__insert_type('wires', s) 
        except RedeclarationError,e:
            # 已经插入过的线网，如果再次插入，直接保持原模原样不动就好了
            print e, "|| so no wire get changed."
            return None
        return s
        
    def insert_assign(self, target, driver, force = False):
        '''@param: target， driver两个signal对象
                    force , 决定在已经有意个target.name
                     赋值的情况下是否强制插入一个新的assign
           @return: 插入成功的assign
        '''
        assert isinstance(target, cc.signal)
        assert isinstance(driver, cc.signal)
        #TODO:添加assign的具体功能，与原来的线网有关系吗
        if self.search_wire( driver.name ) is None:
            self.insert_wire(driver)
        if self.search_wire( target.name) is None:
            self.insert_wire( target )
        assign = cc.assign(left_signal = target, right_signal = driver)
        try:
            self.__insert_type("assigns", assign, "name")
        except RedeclarationError, e:
            if force:
                self._assigns[ target.name ] = assign
                self.assigns.append( assign )
                print "Inserted Forcelly"
                return assign
            else:
                print e, "|| so no assign inserted"
                return None
        else:
            return assign

    # 输出组的方法
    def write(self, path):
        if not os.path.exists( path ):
            os.makedirs( path )
        filename = os.path.join(path, self.top_module.name)+".v"
        try:
            fobj = open(filename,'w')
        except Exception,e:
            print e
            return False
        else:
            console = sys.stdout
            sys.stdout = fobj
            print self.top_module
            for port in self.ports:
                port.__print__(pipo_decl = True)
            for wire in self.wires:
                wire.__print__(is_wire_decl = True)
            for prim in self.primitives:
                print prim
            for assign in self.assigns:
                print assign
            print "endmodule"
            sys.stdout = console
            fobj.close()

if __name__ == "__main__":

    fname = raw_input("plz enter file name>")
    info = vm_parse( fname)
    netlist    = Netlist(info)
    print "Cellref in netlist: ", netlist.cellrefs