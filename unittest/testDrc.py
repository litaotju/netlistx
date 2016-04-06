import unittest
import os

from netlistx import vm_parse
from netlistx.exception import CircuitGraphError
from netlistx.netlist import Netlist
from netlistx.netlist_rules import check
from netlistx.netlist_util import mark_the_circut

class Test_testDrc(unittest.TestCase):

    def setUp(self):
        path = os.path.dirname(__file__)+"\\rules"
        self.path = path

    def test_Succ(self):
        vminfo = vm_parse(self.path + "\\b01.v")
        mark_the_circut( vminfo['m_list'])
        nt = Netlist(vminfo )
        check(nt)

    def test_2CLk(self):
        vminfo = vm_parse(self.path + "\\b011.v")
        mark_the_circut( vminfo['m_list'])
        nt = Netlist(vminfo )
        self.assertRaises(CircuitGraphError, check(nt) )

    def test_Noclk(self):
        vminfo = vm_parse(self.path + "\\b01noclk.v")
        mark_the_circut( vminfo['m_list'])
        nt = Netlist(vminfo )
        check(nt)

if __name__ == '__main__':
    unittest.main()
