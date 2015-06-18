import os
import os.path
import re
import netlist_util as nu
import file_util as fu
#import generate_testbench as gt
#############################################################################################
def insert_scan_chain(fname,verbose=False,presult=True,\
                input_file_dir=os.getcwd(),output_file_dir=os.getcwd(),\
                K=6):
    input_file=os.path.join(input_file_dir,fname)    
    
    #file -->> m_list
    signal_list,m_list,defparam_list=fu.extract_m_list(input_file,verbose)
    
    #m_list -->>all info need 
    all_fd_dict                          =nu.get_all_fd(m_list,verbose)
    all_lut_dict,all_lut_cnt             =nu.get_all_lut(m_list,verbose) 
    #gt.generate_testbench(m_list[0],fd_cnt=len(all_fd_dict),output_dir=output_file_dir)
    lut_out2_FD_dict,FD_din_lut_list        =nu.get_lut_cnt2_FD(m_list,all_fd_dict,verbose,K)    
    ce_signal_list,fd_has_ce_list           =nu.get_ce_in_fd(all_fd_dict,verbose)
    lut_cnt2_ce                             =nu.get_lut_cnt2_ce(m_list,ce_signal_list,K)
    
    fd_ce_cnt=len(fd_has_ce_list)
    #####################################################################    
    #some string constant nedd to add before a FD line
    sen ='    .SCAN_EN(scan_en),\n'
    sin ='    .SCAN_IN'
    sout='    .SCAN_OUT'
    module_ports_decl='  scan_en,\n  scan_in,\n  scan_out,\n'
    in_out_put_del   ='input scan_en;\ninput scan_in;\noutput scan_out;\n'
    wire_del='wire scan_en,scan_in,scan_out;\n'
    
    #some global variable in this function
    scan_in=[]
    scan_out=[]    
    fd_state=False
    current_fd=None
    
    edit_lut_state='IDLE'  #('IDLE','ADD_MUX','ADD_OR')
    current_lut=None
    
    counter=0
    #cnt for debug only
    lut_port_num=0  
    ce_gated_cnt=0
    fd_replace_cnt=0
    cnt_edited_lut=0
    cnt_edited_lut_port=0
    cnt_edited_lut_para=0
    #cnt for debug only 
    
    ##get all lines ready for match and do
    all_lines=fu.remove_comment(input_file,verbose)
    name_base=os.path.splitext(fname)[0]
    output_file=os.path.join(output_file_dir,name_base+'_insert_scan_chain.v')
    try:
        fobj=open(output_file,'w')
    except IOError,e:
        print "Error: file open error:",e
        return False
    fobj.writelines('`include "E:/ISE_WORKSPACE/scan_lib/scan_cells.v"') 
    #####################################################################
    for x in all_lines:
        #top module region
        if  re.match('^\s*module\s+([^\s]+)',x) is not None:
            print 'Note:Find the top module:'+re.match('^\s*module\s+([^\s]+)',x).groups()[0]
            x="  module "+re.match('^\s*module\s+([^\s]+)',x).groups()[0]+"_scan  (\n"
            fobj.writelines(x)
            fobj.writelines(module_ports_decl)
        #top module decl end
        elif x[0]==';':
            fobj.writelines(x)
            fobj.writelines(in_out_put_del)
            fobj.writelines(wire_del)
        #before end of whole module
        elif x[0:10]=='endmodule ':
            for eachCe in  ce_signal_list:
                gated_ce='gated_'+re.sub('[\\\.\[\]\s]','_',eachCe)
                fobj.writelines('assign '+gated_ce+'=scan_en?1\'b1:'+eachCe+' ;\n')
            fobj.writelines('assign scan_in1=scan_in ;\n')
            for eachScan_in in scan_in[1:]:
                fobj.writelines('assign '+eachScan_in+'='+scan_out[scan_in.index(eachScan_in)-1]+' ;\n')
            sout_assign='assign scan_out='+scan_out[-1]+' ;\n'
            fobj.writelines(sout_assign)
            fobj.writelines(x)
        ######################################################################
        else:
            match_fd=re.match('^\s*(FD\w*)\s+([^\s]+)',x)
            match_lut=re.match('^\s*(LUT[1-6]\w*)\s+([^\s]+)',x)
            match_defparam=re.match('\s*(defparam)\s+([^\s]+)\s*(.INIT=)([1-9]+)\'h([0-9A-F]+)\;',x)
            match_ce_signal=re.match('\s*\.CE\((.+)\)(\,?)',x)
            ######################################################################
            #replace the FD with a SCAN_ version or just record the Q output
            if match_fd is not None: 
                current_fd=match_fd.groups()[1]
                fd_state=True
                if match_fd.groups()[1] not in FD_din_lut_list:
                    fd_replace_cnt=fd_replace_cnt+1
                    counter=counter+1
                    x='  SCAN_'+x[2:]
                    fobj.writelines(x)
                    #scan_en
                    fobj.writelines(sen)                     
                    #scan_in this is just the simple version of scan oder
                    #the scan_in of a FD is the scan_out of last find FD  
                    fobj.writelines(sin+'(scan_in'+str(counter)+'),\n')
                    #scan_out
                    fobj.writelines(sout+'(scan_out'+str(counter)+'),\n')
                    scan_in.append('scan_in'+str(counter))
                    scan_out.append('scan_out'+str(counter))
                else:
                    fobj.writelines(x)
            elif ((match_ce_signal is not None) and (fd_state==True)):
                fd_state=False 
                ce_gated_cnt=ce_gated_cnt+1
                fd_has_ce_list.remove(current_fd)
                if match_ce_signal.groups()[0] in ce_signal_list:
                    gated_ce_assign='gated_'+re.sub('[\\\.\[\]\s]','_',match_ce_signal.groups()[0])
                    x='  .CE('+gated_ce_assign+')'+match_ce_signal.groups()[1]+'\n'                 
                    fobj.writelines(x)
            ######################################################################    
            #if find a lut record the info and do add port before the LUT LO port
            elif match_lut is not None:
                assert edit_lut_state=='IDLE'
                current_lut=match_lut.groups()[1]
                lut_port_num=int(match_lut.groups()[0][3])
                if current_lut in lut_out2_FD_dict.keys():
                    edit_lut_state='ADD_MUX'
                    cnt_edited_lut=cnt_edited_lut+1                
                    counter=counter+1
                    assert lut_port_num<=(K-2),"ADD_MUX LUT has more the %d PORTS %s" %(K-2,current_lut)
                    x=re.sub('LUT[1-4]',('LUT'+str(lut_port_num+2)),x)
                    fobj.writelines(x)
                elif current_lut in lut_cnt2_ce:
                    edit_lut_state='ADD_OR'
                    assert lut_port_num<=K-1,"ADD_OR LUT has more the %d PORTS %s" %(K-1,current_lut)
                    x=re.sub('LUT[1-5]',('LUT'+str(lut_port_num+1)),x)
                    fobj.writelines(x)
            elif re.match('\s*\.LO\(|\s*\.O\(',x) is not None:
                if edit_lut_state=='ADD_MUX':
                    cnt_edited_lut_port=cnt_edited_lut_port+1                
                    fobj.writelines('    .I'+str(lut_port_num)+'(scan_in'+str(counter)+'),\n')
                    fobj.writelines('    .I'+str(lut_port_num+1)+'(scan_en),\n')
                    fobj.writelines(x)
                    scan_in.append('scan_in'+str(counter))
                    scan_out.append(all_fd_dict[lut_out2_FD_dict[current_lut][1]][1])
                    lut_port_num=0
                elif edit_lut_state=='ADD_OR':
                    fobj.writelines('    .I'+str(lut_port_num+1)+'(scan_en),\n')
                    fobj.writelines(x)
                    
            ######################################################################
            #edit the LUT defparam for PORT_ADDED LUT
            elif match_defparam is not None:
                old_init=match_defparam.groups()[4]
                if edit_lut_state=='ADD_MUX':
                    edit_lut_state='IDLE'
                    cnt_edited_lut_para=cnt_edited_lut_para+1                
                    lut_port_num=(lut_out2_FD_dict[match_defparam.groups()[1]][0])
                    assert (match_defparam.groups()[1] in lut_out2_FD_dict.keys())
                    assert lut_port_num<=(K-2),"Error:find a LUT has %d port in lut_out2_FD_dict" % lut_port_num
                    if lut_port_num==1:
                        assert  (match_defparam.groups()[3]=='2' and old_init=="1"),\
                        "Error:find LUT1 .INIT !=2'h1 %s" % match_defparam.groups()[1]
                        NEW_INIT="8'hC5"
                    else:
                        NEW_INIT=str(2**(lut_port_num+2))+'\'h'+'F'*int(2**(lut_port_num-2)) \
                        +'0'*int(2**(lut_port_num-2))+old_init*2
                    x=re.sub('([1-9]+)\'h([0-9A-F]+)',NEW_INIT,x)
                    fobj.writelines(x)
                elif edit_lut_state=='ADD_OR':
                    edit_lut_state='IDLE'
                    if lut_port_num==1:
                        NEW_INIT="4'hD"
                    else:
                        NEW_INIT=str(2**(lut_port_num+1))+'\'h'+'F'*int(2**(lut_port_num-2))\
                                +old_init
                    x=re.sub('([1-9]+)\'h([0-9A-F]+)',NEW_INIT,x)
            else:
                fobj.writelines(x)
    #####################################################################
    #print the nessecery info before function e
    if verbose:
        for eachScan_in in scan_in:
            print eachScan_in
        for eachScan_out in scan_out:
            print eachScan_out
    #######close the file handle
    fobj.close()
    for eachFdce in fd_has_ce_list:
        print eachFdce
    assert fd_ce_cnt==ce_gated_cnt,"Some CE didnot gated fully %d != %d!!"%(fd_ce_cnt,ce_gated_cnt)
    assert (fd_replace_cnt+cnt_edited_lut)==len(all_fd_dict),"not all the FD has been scaned !!"
    assert (cnt_edited_lut==cnt_edited_lut_port and cnt_edited_lut==cnt_edited_lut_port),\
            "Some LUT didnot editted fully !!"
    if presult:
        print 'Info:LUT cnt is      : '+str(len(all_lut_dict.keys()))
        print 'Info:LUT1-6 number is: '+str(all_lut_cnt)
        print 'Info:FD CNT is       : '+str(counter)+":::"+str(len(all_fd_dict))
        print 'Info:replace FD CNT  : '+str(fd_replace_cnt)
        print 'Info:Useful LUT CNT  : '+str(len(FD_din_lut_list))
        print 'Info:edited LUT CNT  : '+str(cnt_edited_lut)+':::'+str(cnt_edited_lut_port)+':::'+str(cnt_edited_lut_port)
        print 'Info:FD has a CE CNT : '+str(fd_ce_cnt)
        print 'Info:ce_signal CNT is: '+str(len(ce_signal_list))
    print 'Job: Replace '+fname+' done\n\n'
    return True

#############################################################################################
if __name__=='__main__':    
    parent_dir=os.getcwd()
    while(1):
        tmp1=raw_input('Plz enter the verilog source sub dir:')
        input_file_dir=parent_dir+"\\test_input_netlist\\"+tmp1
        if os.path.exists(input_file_dir)==False:
            print 'Error : this dir dont exists!'
            continue
        else:
            break
    while(1):
        tmp2=raw_input('Plz enter the output sub dir:')
        output_file_dir=parent_dir+"\\test_output_dir\\"+tmp2
        if os.path.exists(output_file_dir)==False:
            print 'the dir: '+output_file_dir+' dont exists'
            flag=os.mkdir(output_file_dir)
            print 'create a dir : '+output_file_dir
            break 
        else:
            continue           
    K=int(raw_input('plz enter the K parameter of FPGA:K='))        
    print "Note: current path: "+parent_dir
    print "Note: output_file_path: "+output_file_dir
    print "Note: input_file_path: "+input_file_dir
    for eachFile in os.listdir(input_file_dir):
        print  eachFile
        if os.path.splitext(eachFile)[1]=='.v':
            insert_scan_chain(eachFile,False,True,input_file_dir,output_file_dir,K)
        else:
            continue


