import os
import os.path
import netlist_util as nu
import re
#############################################################################################
def full_replace_scan_chain(fname,verbose=True,input_file_dir=os.getcwd(),output_file_dir=os.getcwd()):
    input_file=os.path.join(input_file_dir,fname)
    all_lines=nu.remove_comment(input_file,False)
    
    name_base=os.path.splitext(fname)[0]
    output_file=os.path.join(output_file_dir,name_base+'_scan_full_replace.v')
    try:
        fobj=open(output_file,'w')
    except IOError,e:
        print "Error: file open error:",e
        return False          
    #add the include file @begin of a verilog design file
    fobj.writelines('`include "E:\ISE_WORKSPACE\scan_lib\scan_cells_ce_gated.v"') 
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
    for x in all_lines:
        #top module region
        if  re.match('^\s*module\s+([^\s]+)',x) is not None:
            print 'Note:Find the top module:'+re.match('^\s*module\s+([^\s]+)',x).groups()[0]
            fobj.writelines(x)
            fobj.writelines(module_ports_decl)
        elif x[0]==';':
            fobj.writelines(x)
            fobj.writelines(in_out_put_del)
            fobj.writelines(wire_del)
        elif x[0:10]=='endmodule ':
            fobj.writelines('assign scan_out=scan_out'+str(counter)+' ;\n')
            fobj.writelines(x)    
        ######################################################################
        #FD replace
        elif re.match('^\s*(FD\w*)\s+([^\s]+)',x) is not None:
            #replace the FD with a SCAN_ version or just record the Q output
            counter=counter+1
            x='  SCAN_'+x[2:]
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
    if verbose:
        print "Note:full replace %d FD in file %s" %(counter,fname)
    #######close the file handle
    fobj.close()
    print 'Job: Replace '+fname+' done\n\n'
    return True

#############################################################################################
if __name__=='__main__':    
    parent_dir=os.getcwd()
    input_file_dir=parent_dir+"\\test_input_netlist\\bench_virtex4"
    output_file_dir=parent_dir+"\\test_output_dir\\bench_full_replace_virtex4"    
    print output_file_dir
    print parent_dir
    print input_file_dir   
    for eachFile in os.listdir(input_file_dir):
        print eachFile
        if os.path.splitext(eachFile)[1]=='.v':
            full_replace_scan_chain(eachFile,False,input_file_dir,output_file_dir)
        else:
            continue
