# -*-coding:utf-8 -*- #
import re
import os
import sys

import networkx as nx

from netlistx.netlist import Netlist
from netlistx.file_util import vm_files, StdOutRedirect
from netlistx.class_circuit import *

from netlistx.parser.netlist_parser import vm_parse
from netlistx.graph.cloudgraph import CloudRegGraph
from netlistx.graph.circuitgraph import get_graph, CircuitGraph
from netlistx.scan.partialOpt import get_scan_fds

path = raw_input("plz enter path>")
for vm in vm_files(path):
    fname = os.path.join(path, vm)
    info = vm_parse( fname)
    netlist    = Netlist(info)
    #nr.check(netlist, check_reset = False)
    g = CircuitGraph(netlist)
    cr = CloudRegGraph( g )
    cr.info()
    scan_fds = get_scan_fds(cr, path)

    used_lut = {}
    useful_lut_for_partial_scan = 0
    for fd in scan_fds:
        assert fd in netlist.primitives
        assert g.predecessors(fd)
        for entity in  g.predecessors_iter(fd):
            if isinstance(entity, circut_module) and entity.m_type == "LUT":
                #print "LUT %d found" % entity.input_count()
                if entity.input_count() <= 4:
                    if not used_lut.has_key(entity):
                        used_lut[entity] = 0
                        useful_lut_for_partial_scan += 1
                    else:
                        used_lut[entity] += 1
    with StdOutRedirect( os.path.join(path, cr.name+"_scan_count.txt")):
        print "Partial Scan: ", len(scan_fds)
        print "Logic Fusion partial scan:", useful_lut_for_partial_scan
        print os.linesep.join( ( lut.cellref for lut in used_lut ) )