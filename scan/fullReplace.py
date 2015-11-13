import os
import os.path
import re

# user-defined module
import netlistx.netlist_util as nu

#扫描D触发器的库的位置
scanlib = '`include "E:\ISE_WORKSPACE\scan_lib\scan_cells_ce_gated.v"'

def full_replace_scan_chain(fname,verbose=True,input_file_dir=os.getcwd(),output_file_dir=os.getcwd()+"\\out\\"):
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
    header = scanlib
    fobj.writelines( header ) 
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

#############################################################################################
if __name__=='__main__':    
    parent_dir=os.getcwd()
    input_file_dir = parent_dir+"\\test\\bench_virtex4"
    output_file_dir = parent_dir+"\\test\\bench_full_replace_virtex4"    
    if not os.path.exists( output_file_dir ):
        os.mkdir(output_file_dir )
    print "CWD:", parent_dir
    print "Output to", output_file_dir
    print "Input netlist:", input_file_dir   
    for eachFile in os.listdir(input_file_dir):
        print "Handling:", eachFile, "..."
        if os.path.splitext(eachFile)[1] in ['.v', '.vm']:
            full_replace_scan_chain(eachFile,\
                     False, input_file_dir, output_file_dir)