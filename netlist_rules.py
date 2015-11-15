# -*- coding:utf-8 -*-

from netlistx.exception import *
from netlistx.netlist import Netlist


def check(nt):
    '''
    '''
    check_ports =  ['C','R','S','CLR','PRE']
    specials = _get_fd_specport( nt, check_ports)

    clks = specials['C']
    sync_resets  = specials['R'].keys() + specials['S'].keys()
    async_resets = specials['CLR'].keys() + specials['PRE'].keys()
    
    _clk_check(nt, clks)
    _reset_check( sync_resets + async_resets)


def _get_fd_specport(nt, port_names ):
    '''@param: nt, a Netlist obj
       @return: specs, a dict, {port_name:{signal_id : [fd list]} }
    '''
    assert isinstance(nt, Netlist)
    fds = [prim for prim in nt.primitives if prim.m_type == 'FD']
    specs = {name:{} for name in port_names }
    for fd in fds:
        for port in fd.port_list:
            name = port.port_name
            if name in port_names:
                signal_id = port.port_assign.string
                if not specs[name].has_key( signal_id ):
                    specs[name][ signal_id ] = [fd]
                else:
                    specs[name][ signal_id ].append( fd )
    return specs

def _clk_check(nt, clks):
    if len(clks) > 1:
        errmsg =  "Netlist has %s CLK domain.They are: %s" % ( len(clks), clks.keys() )
        raise CircuitGraphError, errmsg
    elif len(clks) == 0:
        print "Info: no clks in this netlist"
        return None
    clkname = clks.keys()[0]
    clkflag = False
    single_inports = []
    for port in nt.ports:
        if port.port_type == "input":
            single_inports += port.split()
    for port in single_inports:
        if port.port_assign.string == clkname:
            clkflag = True
            break
        else: continue
    if not clkflag:
        errmsg = "CLK: %s do not connected to any pi" % clkname
        raise CircuitGraphError, errmsg 

def _reset_check(resets):
    pass