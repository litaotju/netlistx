import unittest
import os

import netlistx.circuit as cc
from netlistx.parser.netlist_parser import vm_parse
from netlistx.netlist import Netlist
from netlistx.scan.instrumentor import FusionInstrumentor, FullReplaceInstrumentor

class Test_FusionIntrumentor(unittest.TestCase):
    
    def setUp(self):
        super(Test_FusionIntrumentor, self).setUp()
        vmfile = os.path.join(os.path.dirname(__file__),"b01.v")
        netlist = Netlist(vm_parse(vmfile))
        replace_dffs = filter(lambda x: cc.isDff(x), netlist.primitives)
        self.instrumentor = FusionInstrumentor(netlist, replace_dffs, [], 6)
        self.netlist = netlist

    def test_insert_scan(self):
        self.instrumentor.insert_scan()
        self.netlist.top_module.name += "_scan"
        self.netlist.write(os.path.dirname(__file__))

if __name__ == '__main__':
    unittest.main()
