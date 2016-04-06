# -*-coding:utf-8 -*- #
import re
import os
import sys

import networkx as nx

from netlistx.netlist import Netlist
from netlistx.file_util import vm_files, StdOutRedirect
from netlistx.circuit import *

from netlistx.parser.netlist_parser import vm_parse
from netlistx.graph.circuitgraph import get_graph, CircuitGraph
from netlistx.graph.cloudgraph import CloudRegGraph

#两种部分扫描的方法opt & blas
import netlistx.scan.partialOpt as opt
import netlistx.scan.partialBallast as blas


'''直接运行本脚本, 可生成FCCM 16 文章中的数据
'''

#FPGA 常数K, 与计算cost有关
K = 6

def get_scan_records():
    '''比较 BALLAST，OptPartialScan, OptPlusFusion 
      几种部分扫描的触发器数量， 以及可以利用已有LUT插入扫描的触发器。
      返回Record
    '''
    path = raw_input("plz enter path>")
    records = [] # record the scan number of each circuit
    for vm in vm_files(path):
        fname = os.path.join(path, vm)
        info  = vm_parse( fname)
        netlist    = Netlist(info)
        #nr.check(netlist, check_reset = False)
        g = CircuitGraph(netlist)              
        cr = CloudRegGraph( g )
        cr2 = CloudRegGraph( g )
        cr.info()

        #两种部分扫描
        opt_scan_fds = opt.get_scan_fds(cr, path)
        blas_scan_fds = blas.ballast(cr2)
        #部分扫描中可以利用的LUT
        useful_lut_for_partial_scan = get_useful_luts(opt_scan_fds, g, K)

        is_lut = lambda prim: True if prim.m_type == "LUT" else False
        is_fd  = lambda prim: True if prim.m_type == "FD" else False
        fds = filter(is_fd, netlist.primitives)
        luts = filter(is_lut, netlist.primitives)
        with StdOutRedirect( os.path.join(path, cr.name + "_scan_count.txt")):
            print "All_FD_number           : ", len( fds )
            print "ALL_LUT_number          : ", len( luts )
            print "FULL_replace_cost_LUT   : ", get_cost( fds )

            print "BALLAST_Scan_FD         : ", len(blas_scan_fds)
            print "BALLAST_cost_LUT        : ", get_cost(blas_scan_fds)

            print "Opt_Partial_Scan_FD     : ", len(opt_scan_fds)
            print "Opt_Partial_cost_LUT    : ", get_cost( opt_scan_fds )

            print "Opt_PartialFusion_Cost  : ", get_cost( opt_scan_fds ) - len(useful_lut_for_partial_scan)
            print "#Useful_LUT_for_opt_partial_SCAN: ", len(useful_lut_for_partial_scan)
            record = ( netlist.top_module.name,
                            len( fds ),
                            len(luts),
                            get_cost(fds),

                            len(blas_scan_fds),
                            get_cost(blas_scan_fds),
                            
                            len(opt_scan_fds),
                            get_cost( opt_scan_fds ),

                            get_cost(opt_scan_fds) - len(useful_lut_for_partial_scan ),
                            len(useful_lut_for_partial_scan )
                     ) 
            records.append( record )
    return records

def get_useful_luts(scan_fds, g, K):
    '''@param: scan_fds, a itreable sequence of all the scan_fds primtive
               g,        a  CircuitGraph obj
       @return: useful_luts, a {}, key is all the luts useful for scan in the circuit
    '''
    # 使用字典表明每一个LUT只被利用了一次，因为字典的键是唯一的
    useful_luts = {}
    other_dff_ports = set( ["CE", "R", "CLR", "S", "PRE" ] )
    for fd in scan_fds:
        assert g.predecessors(fd)
        for entity in g.predecessors_iter(fd):
            if isinstance(entity, circut_module) and entity.m_type == "LUT":
                port_pairs = g[entity][fd]['port_pairs']
                fd_ports = set( pair[1].port_name for pair in port_pairs  )
                if len(fd_ports) > 1:
                    print "MultiConnect LUT-FD: %s %s, %d" % (entity.name, fd.name, len(fd_ports) )
                if ( ("D" in fd_ports) and entity.input_count() <= K-2 ) \
                        or ( other_dff_ports.intersection(fd_ports) and entity.input_count() <= K-1) :
                    if not useful_luts.has_key(entity):
                        useful_luts[entity] = 0
                    else:
                        useful_luts[entity] += 1
    return useful_luts

def get_cost(fds):
    return sum( [ fd.input_count() for fd in fds ] )

if __name__ == "__main__":
    fname = raw_input("plz enter record file name >")
    rs = get_scan_records()
    with StdOutRedirect(fname):
        print "circuit #FD #LUT #FULL_SCAN_LUT #BALLAST_FD #BALLAST_LUT #OptPartial_FD #OptPartial_LUT #Opt_PartialFusion_LUT_cost #Useful_OptPartialFusion_FD"
        print os.linesep.join( [ ("%s %d %d %d %d %d %d %d %d %d" % record) for record in rs] )