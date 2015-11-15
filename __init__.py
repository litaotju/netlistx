# -*- coding:utf-8 -*-

__author__ = ["litao"]
__verson__ = "0.0.1"

#__all__ = [
#        # package
#        "netlist_parser" , 
        
#        # modules
#        "ballast",
#        "circuitgraph",
#        "class_circuit",
#        "crgraph",
#        "exception",
#        "file_util",
#        "graph_top",
#        "graph_util",
#        "netlist",
#        "netlist_util",
#        "scan_chain_full_replace",
#        "scan_chain_insert",
#        "sgraph",
#        "testbench_generate"
#    ]

# 所有的 Exception都直接导入到包的顶层
import exception
from exception import *

# 进行网表的解析有两种方法。 1.导入parser模块 2.直接导入parser模块的vm_parse方法
#import netlistx.parser.netlist_parser as parser
from netlistx.parser.netlist_parser import vm_parse

# 所有与网表相关的类都直接被导入到包的顶层
import class_circuit
from class_circuit import *

from netlistx.graph import *
from netlistx.graph.crgraph import CloudRegGraph
from netlistx.graph.circuitgraph import CircuitGraph

import netlist
from netlist import Netlist

import netlist_util

