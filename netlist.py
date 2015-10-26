# -*- coding:utf-8 -*- #

import netlist_parser.netlist_parser as parser
import class_circuit as cc


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
        # 根据解析器的信息存储
        self.top_module  = vminfo['m_list'][0]
        self.ports       = vminfo['port_decl_list']        
        self.wires       = vminfo['signal_decl_list']
        self.primtives   = vminfo['primitive_list']
        self.assigns     = vminfo['assign_stm_list']
        
        self.others = None
        # 建立一系列字典，提升查询的效率
        self._ports     = self.__build_dict(self.ports,    "name" )
        self._wires     = self.__build_dict(self.wires,    "name" )
        self._primtives = self.__build_dict(self.primtives, "name" )
        self._assigns   = self.__build_dict(self.assigns,   "name" )

        print "Note: Bulid Netlist Obj sucessfully"
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
            assert key is not None
            if not tdict.has_key(key):
                tdict[ key ] = obj
            else:
                errmsg = "Error: Redecleration of %s obj : %s" \
                        % (obj.__class__ , key )
                raise Exception, errmsg
        return tdict

    def __search_dict(self, dict_name, target):
        '''@param: dict_name, self的一个字典数据属性
                    target, 一个ID
           @return: None或者dict_name中的一个值
        '''
        try:
            dict = getattr(self, dict_name)
        except AttributeError:
            errmsg = "Error: netlist has no attr %s" % dict_name
            raise Exception, errmsg
        try:
            result = dict[target]
        except KeyError:
            return None
        else:
            return result
          
    # 查询组的方法
    def top(self):
        return self.top_module
 
    def search_port(self, name):
        return self.__search_dict("_ports", name )

    def search_wire(self, name):
        return self.__search_dict("_wires", name)

    def search_prim(self, name):
        return self.__search_dict("_primtives", name )
    
    def search_assign(self, name):
        return self.__search_dict("_assigns", name )

    # 修改组的方法
    def insert_prim(self, prim):
        '''@param: prim, a cc.circut_module 对象
        '''
        assert isinstance(prim, cc.circut_module)
        has_prim = self.search_prim( prim.name ) 
        if has_prim is not None:
            errmsg = "Error: a prim has the same name already in netlist."
            raise Exception, errmsg
        else:
            self.primtives.append( prim )
            self._primtives[prim.name] = prim
        try:
            p_assigns = prim.port_assign_list
        except AttributeError:
            print "Warning: prim has no port_assigns "
        else:
            if len( p_assigns)==0:
            #TODO: raise an exception,for this 
                print "Warning: A prim with no port inserted"
            else:
                for signal in p_assigns:
                    self.insert_wire( signal )

    def insert_wire(self, signal):
        assert isinstance(signal, cc.signal)
        has_signal = self.search_wire(signal.name)
        if has_signal is not None:
            errmsg = "Error: a signal has the same name already in netlist"
            raise Exception, errmsg
        else:
            self.wires.append( signal)
            self._wires[signal.name] = signal
    
    def insert_assign(self, assign, left, right):
        pass


    # 加入扫描链的方法
    def scan_insert(self):
        pass

    # 输出组的方法
    def write(self, path):
        pass

   
def __test():
    from file_util import vm_files
    path = raw_input("plz enter a path:")
    for vm in vm_files(path):
        vminfo = parser.vm_parse( path+"\\"+vm )
        n1 = Netlist(vminfo)
        x = cc.circut_module()
        n1.insert_prim(x)

if __name__ == "__main__":
    __test()