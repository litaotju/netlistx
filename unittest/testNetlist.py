# -*-coding:utf-8 -*- #

#dependency
import sys
import os
import unittest

# user defined module
import netlistx
from netlistx import *

class testNetlist(unittest.TestCase):
    
    def setUp(self):
        path = os.path.dirname(__file__)+"\\netlist"
        self.normal = path + "\\normal.vm"
        self.redecl = path + "\\redecl.vm"
        self.path = path

    def testRecl(self,):
        vminfo = vm_parse(self.redecl)
        self.assertRaises(RedeclarationError, Netlist, vminfo)
        print "Redeclaration Handle OK"
    
    def testInit(self, ):
        vminfo  = vm_parse(self.normal)
        nt = Netlist(vminfo)
        print "test Netlist __init__ OK"

    def testSearch(self,):
        vminfo  = vm_parse(self.normal)
        n1 = Netlist(vminfo)

        # 查找已经肯定存在的元素，确保返回值不是None且是特定的对象
        self.assertEqual( n1.search_wire('line1'), signal(name='line1') )
        self.assertIsNotNone( n1.search_prim("\stato_16_1_iv_i_cZ[2]") )
        self.assertIsNotNone( n1.search_port("reset"))
        self.assertIsNotNone( n1.search_assign("GND") )

        self.assertIsInstance( n1.search_wire("stato_16_1_iv_i"), signal )
        self.assertIsInstance( n1.search_prim("\stato_Z[0]"), circut_module)
        self.assertIsInstance( n1.search_port("overflw"), port )
        self.assertIsInstance( n1.search_assign( "VCC"), assign )

        # 查找不存在的元素，确保返回None值而已
        self.assertIsNone( n1.search_port("NNNN")    )
        self.assertIsNone( n1.search_wire("NOECISS") )
        self.assertIsNone( n1.search_assign("NIHAI") )
        self.assertIsNone( n1.search_prim("ThisISS") )

    def testInsert(self,):
        vminfo  = vm_parse(self.normal)
        n1 = Netlist(vminfo)
        
        prim = circut_module('NewPrim','FD', 'FDC')
        sD = signal(name = "sD")
        pD = port('D', 'input', sD)
        prim.add_port_list( [pD] )

        # 插入不存在的元素报成功，且返回元素本身。
        self.assertIs(n1.insert_prim(prim), prim)
        # 已经加入过的wire
        self.assertIsNone( n1.insert_wire(sD) )
        # 加入格式错误的字符串wire
        self.assertRaisesRegexp(FormatError, "param type error: not a signal or a string.",
                                n1.insert_wire, 22000)
        self.assertRaises(AssertionError, n1.insert_wire, "Error Formart2" )
        # 加入正确的字符串wire
        self.assertEqual(n1.insert_wire("Nnew [3:0]"), n1.search_wire("Nnew"))
        
        #加入正确的assign


    def testTop(self):
        vminfo  = vm_parse(self.normal)
        n1 = Netlist(vminfo)
        top =  n1.get_top()
        self.assertIsInstance(top, circut_module)
        self.assertEqual(len(top.port_list) ,6)

        port5 = top.port_list[5]
        self.assertIsInstance( port5, port)
        self.assertEqual(port5.port_assign, signal('input','clock'))

    def testWrite(self):
        vminfo  = vm_parse(self.normal)
        n1 = Netlist(vminfo)
        n1.write(self.path)

if __name__ == "__main__":
    unittest.main()