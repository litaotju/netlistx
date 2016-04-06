import os
import unittest

import netlistx.graph.cloudgraph as newcr
import netlistx.graph.crgraph as oldcr
from netlistx.graph.circuitgraph import get_graph
from netlistx.file_util import vm_files

class Test_testCloud(unittest.TestCase):
    
    def setUp(self):
        self.path = raw_input("Set vmfile directory:")

    def test_A(self):
        for eachVm in vm_files(self.path):
            inputfile =os.path.join(self.path, eachVm)
            g2 = get_graph( inputfile )
            g2.info()
            crnew = newcr.CloudRegGraph(g2) 
            crold = oldcr.CloudRegGraph(g2)
            self.assertEqual( crnew.number_of_edges(), crold.number_of_edges() )

if __name__ == '__main__':
    unittest.main()
