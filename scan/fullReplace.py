# -*-coding:utf-8 -*-

import os
import os.path
import re

# user-defined module
import netlistx.netlist_util as nu
from netlistx.scan.config import SCAN_LIB

def full_replace_scan_chain(fname,
                            verbose=True,
                            input_file_dir=os.getcwd(),
                            output_file_dir=os.getcwd()+"\\out\\"):
    input_file = os.path.join(input_file_dir, fname)
    name_base = os.path.splitext(fname)[0]
    output_file = os.path.join(output_file_dir,fname)
    try:
        infile = open( input_file, 'r')
        fobj = open( output_file, 'w' )
    except IOError, e:
        print "Error: file open error:",e
        return False          
    #add the include file @begin of a verilog design file
    fobj.writelines( SCAN_LIB )
    #####################################################################    
    #some string constant nedd to add before a FD line
    sen ='    .SCAN_EN(scan_en),\n'
    sin ='    .SCAN_IN'
    sout='    .SCAN_OUT'
    module_ports_decl='  scan_en,\n  scan_in,\n  scan_out,\n'
    in_out_put_del   ='input scan_en;\ninput scan_in;\noutput scan_out;\n'
    wire_del='wire scan_en,scan_in,scan_out;\n'
     
    #counter for the FD number
    counter=0
    #####################################################################
    for x in infile:
        if x.lstrip()[0:2] == "//":
            continue
        #top module region
        if  re.match('^\s*module\s+([^\s]+)',x) is not None:
            print 'Info: Find the top module:'+re.match('^\s*module\s+([^\s]+)',x).groups()[0]
            fobj.writelines(x)
            fobj.writelines(module_ports_decl)
        elif x[0]==';':
            fobj.writelines(x)
            fobj.writelines(in_out_put_del)
            fobj.writelines(wire_del)
        elif x.lstrip().startswith('endmodule'):
            fobj.writelines('assign scan_out=scan_out'+str(counter)+' ;\n')
            fobj.writelines(x)    
        ######################################################################
        #FD replace
        elif re.match('^\s*(FD\w*)\s+([^\s]+)', x) is not None:
            #replace the FD with a SCAN_ version or just record the Q output
            counter = counter + 1
            x = " "*4 + 'SCAN_' + x.lstrip()
            fobj.writelines(x)
            fobj.writelines(sen)                     
            #scan_in this is just the simple version of scan oder
            #the scan_in of a FD is the scan_out of last find FD
            if counter==1:
                fobj.writelines(sin+'(scan_in),\n')
            else:
                fobj.writelines(sin+'(scan_out'+str(counter-1)+'),\n')
            fobj.writelines(sout+'(scan_out'+str(counter)+'),\n')
        else:
            fobj.writelines(x)

    #####################################################################
    #print the nessecery info before function e
    fobj.close()
    print "Info: full replace %d FD in file %s" %(counter,fname)
    print 'Job:  Replace '+fname+' done\n\n'
    return True

if __name__=='__main__':
    print os.getcwd()
    pwd = ""
    while(not os.path.exists(pwd)):
        pwd = raw_input("plz enter vm files path:")
    outpath = os.path.join(pwd,"FULL_REPLACE")
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    vms = [ name for name in os.listdir(pwd) if os.path.splitext(name)[1] in (".v" ,".vm")]
    for vm in vms:
        full_replace_scan_chain(vm, True, pwd, outpath)
