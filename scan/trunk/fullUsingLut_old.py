# -*- coding: utf-8 -*-
import sys
import os
import os.path
import re
from exceptions import SystemExit

# user-defined module
import netlistx.netlist_util as nu
import netlistx.class_circuit   as cc
from netlistx.parser.netlist_parser import vm_parse

from netlistx.scan.config import SCAN_LIB2 as SCAN_LIB

#############################################################################################
def insert_scan_chain_new(fname, verbose=False, presult=True,\
                input_file_dir = os.getcwd(), output_file_dir = os.getcwd(),\
                K = 6):
    '''@para: fname ,input file name in current path
             verbose, if True print 调用的各个函数的 redandunt infomation
             presult ,if True 打印最终的各种统计信息
             input_file_dir, default os.getcwd(),
             output_file_dir, default os.getcwd()
    '''
    input_file=os.path.join(input_file_dir , fname)    
    suffix = "_full_scan_using_lut"
    #file -->> m_list
    info = vm_parse( input_file )
    m_list = info['m_list']
    port_decl_list   = info['port_decl_list']
    signal_decl_list = info['signal_decl_list']
    assign_stm_list  = info['assign_stm_list']
   
    nu.mark_the_circut(m_list[1:])
    
    #m_list -->>all info need 
    lut_type_cnt = [0,0,0,0,0,0]
    all_fd_dict  = nu.get_all_fd(m_list, verbose)
    all_lut_dict = nu.get_all_lut(m_list, lut_type_cnt, verbose) 
    
    ##下面两个列表记录了需要进行修改的LUT和D触发器的
    lut_out2_FD_dict,FD_din_lut_list        =nu.get_lut_cnt2_FD(m_list,all_fd_dict,verbose,K)    
    
    ##CE优化所需要的netlist信息
    ce_signal_list,fd_has_ce_list           =nu.get_ce_in_fd(all_fd_dict,verbose)
    lut_cnt2_ce,un_opt_ce_list              =nu.get_lut_cnt2_ce(m_list,ce_signal_list,K,verbose)
    fd_ce_cnt=len(fd_has_ce_list)
    
    #gt.generate_testbench(m_list[0],fd_cnt=len(all_fd_dict),output_dir=output_file_dir)    
    #####################################################################    
    counter=0
    scan_out_list=[]
    gatedce_list = []

    #cnt for debug only
    fd_replace_cnt=0
    cnt_edited_lut=0
    #cnt for debug only 
    
    name_base=os.path.splitext(fname)[0]
    output_file=os.path.join(output_file_dir,name_base + suffix + '.v')
    try:
        fobj=open(output_file,'w')
    except IOError,e:
        print "Error: file open error:",e
        raise SystemExit
    fobj.writelines(SCAN_LIB)
    #--------------------------------------------------------------------------
    #全局信号增加
    #--------------------------------------------------------------------------
    _scan_in=cc.signal('input','scan_in',None)
    _scan_en=cc.signal('input','scan_en',None)
    _scan_out=cc.signal('output','scan_out',None)
    port_scan_in=_scan_in.signal_2_port()
    port_scan_en=_scan_en.signal_2_port()
    port_scan_out=_scan_out.signal_2_port()
    m_list[0].port_list.insert(0,port_scan_in)
    m_list[0].port_list.insert(0,port_scan_out)
    m_list[0].port_list.insert(0,port_scan_en)
    
    print "Info: top module is : ", m_list[0].name 
    #--------------------------------------------------------------------------
    #primitive的修改
    #--------------------------------------------------------------------------
    for eachPrimitive in m_list[1:]:
        ##修改LUT增加MUX,进行扫描功能插入
        if eachPrimitive.m_type=='LUT' and (eachPrimitive.name in lut_out2_FD_dict.keys()):
            counter+=1
            input_num=lut_out2_FD_dict[eachPrimitive.name][0]
            scan_in=cc.port("I"+str(input_num),'input',cc.signal(name="scan_in"+str(counter)))            
            scan_en=cc.port('I'+str(input_num+1),'input',cc.signal(name="scan_en"))            
            eachPrimitive.port_list.insert(-1,scan_in)
            eachPrimitive.port_list.insert(-1,scan_en)
            assert (not eachPrimitive.param_list==None)
            assert len(eachPrimitive.param_list)==1
            old_init=eachPrimitive.param_list[0].value
            init_legal=re.match('(\d+)\'[hb]([0-9A-F]+)',old_init)
            assert (init_legal is not None)
            assert int(init_legal.groups()[0])==2**input_num
            if input_num==1:
                assert  (init_legal.groups()[0]=='2' and init_legal.groups()[1]=="1"),\
                "Error:find LUT1 .INIT !=2'h1 %s, is %s" % (eachPrimitive.name,eachPrimitive.param_list[0].value)
                NEW_INIT="8'hC5"
            else:
                NEW_INIT=str(2**(input_num+2))+'\'h'+'F'*int(2**(input_num-2)) \
                +'0'*int(2**(input_num-2))+(init_legal.groups()[1])*2
            eachPrimitive.param_list[0].edit_param('INIT',NEW_INIT)
            eachPrimitive.cellref=re.sub('LUT[1-4]',('LUT'+str(input_num+2)),eachPrimitive.cellref)
            scan_out_list.append(all_fd_dict[lut_out2_FD_dict[eachPrimitive.name][1]]['Q'].string)
            cnt_edited_lut+=1
        #--------------------------------------------------------------------------
        #未能利用剩余LUT的FD，进行CELL替换，端口增加
        #--------------------------------------------------------------------------  
        elif (eachPrimitive.m_type=='FD') and (eachPrimitive.name not in FD_din_lut_list):
            counter+=1
            eachPrimitive.cellref="SCAN_"+eachPrimitive.cellref
            SCAN_IN=cc.port('SCAN_IN','input',cc.signal(name="scan_in"+str(counter)))
            SCAN_EN=cc.port('SCAN_EN','input',cc.signal(name="scan_en"))
            SCAN_OUT=cc.port('SCAN_OUT','output',cc.signal(name='scan_out'+str(counter)))
            eachPrimitive.port_list.insert(0,SCAN_OUT)
            eachPrimitive.port_list.insert(0,SCAN_EN)
            eachPrimitive.port_list.insert(0,SCAN_IN)
            scan_out_list.append('scan_out'+str(counter))
            fd_replace_cnt+=1
        #--------------------------------------------------------------------------
        #CE时钟使能控制信号的优化     改LUT,进行时钟使能的插入,就是插入一个或门
        #--------------------------------------------------------------------------   
        elif(eachPrimitive.m_type=='LUT') and (eachPrimitive.name in lut_cnt2_ce):
            input_num=int(eachPrimitive.cellref[3])
            scan_en=cc.port('I'+str(input_num),'input',cc.signal(name="scan_en"))
            eachPrimitive.port_list.insert(-1,scan_en)
            assert (not eachPrimitive.param_list==None)
            assert len(eachPrimitive.param_list)==1
            old_init=eachPrimitive.param_list[0].value
            init_legal=re.match('(\d+)\'[hb]([0-9A-F]+)',old_init)
            assert (init_legal is not None)
            assert int(init_legal.groups()[0])==2**input_num
            if input_num==1:
                NEW_INIT="4'hD"
            else:
                NEW_INIT=str(2**(input_num+1))+'\'h'+'F'*int(2**(input_num-2))\
                           +init_legal.groups()[1]
            eachPrimitive.param_list[0].edit_param('INIT',NEW_INIT)
            eachPrimitive.cellref=re.sub('LUT[1-5]',('LUT'+str(input_num+1)),eachPrimitive.cellref)
        #--------------------------------------------------------------------------
        #未能利用剩余LUT的的 FD*E, 在时钟使能信号和LUT的输出之间加入一个或门
        #--------------------------------------------------------------------------
    for eachPrimitive in m_list[1:]:
        if (eachPrimitive.m_type=='FD') and (eachPrimitive.name in fd_has_ce_list):
            current_ce=all_fd_dict[eachPrimitive.name]['CE'].string 
            if current_ce in un_opt_ce_list:
                # if current ce start with \ , there will be a syntax error to synthesis
                # 将新引入的信号改名字应该不会产生问题，原有的信号完全不变，只是把连接到FD的信号
                # 解决方法，加一个gated_ prefix，将其中的信号名称的 ".[]" 全变成 "_",组成新的信号名称
                # 同时，为了防止wire的重复声明，应该将新加的信号存储到一个列表中，不重复声明
                if current_ce[0] == '\\':
                    gatedCE = "gated_"+re.sub("[\[\]\.]","_", current_ce[1:])
                else:
                    gatedCE = "gated_"+re.sub("[\[\]\.]","_", current_ce)
                new_ce_signal=cc.signal('wire',gatedCE)
                eachPrimitive.edit_spec_port('CE',new_ce_signal)
                if not gatedCE in gatedce_list:
                    gatedce_list.append(gatedCE)
                    signal_decl_list.append(new_ce_signal)

    #--------------------------------------------------------------------------
    #扫描链顺序的确定,在结尾处进行assign
    #--------------------------------------------------------------------------
    assign_stm_list.append( cc.assign('assign', cc.signal(name = "scan_in1"),
                                                cc.signal(name = "scan_in")) )
    for i in range(2,counter+1):
        tmp_assign = cc.assign('assign',cc.signal(name = "scan_in"+str(i) ),
                                        cc.signal( name = scan_out_list[i-2] )) 
        assign_stm_list.append( tmp_assign )
    assign_stm_list.append(cc.assign('assign',cc.signal( name = "scan_out"), 
                                cc.signal( name = scan_out_list[counter-1])) )
    
    #--------------------------------------------------------------------------
    #检查是否成功
    #check all the numbers ,insure all wanted LUT and FD been handled
    #--------------------------------------------------------------------------
    assert (fd_replace_cnt+cnt_edited_lut)==len(all_fd_dict),"not all the FD has been scaned !!"
    assert (cnt_edited_lut==len(FD_din_lut_list)),"There is Usefully LUT not edited !!"
    #--------------------------------------------------------------------------
    #进行文件的打印或者直接输出到stdout上面
    #--------------------------------------------------------------------------
    if fobj:
        console=sys.stdout
        sys.stdout=fobj
        m_list[0].print_module()
        for eachPipo in port_decl_list:
            eachPipo.__print__(pipo_decl=True)
        for eachWire in signal_decl_list:
            eachWire.__print__(is_wire_decl=True)
        for eachModule in m_list[1:]:
            assert isinstance(eachModule,cc.circut_module), eachModule
            print eachModule
        if assign_stm_list:
            for eachAssign in assign_stm_list:
                print eachAssign

        for eachCE in un_opt_ce_list:
            if eachCE[0] == '\\':
                gatedCE = "gated_"+re.sub("[\[\]\.]","_", eachCE[1:])
            else:
                gatedCE = "gated_"+re.sub("[\[\]\.]","_", eachCE)
            print "assign %s = scan_en? 1'b1 : %s ;"%(gatedCE, eachCE)
        print "//this is a file generate by @litao"
        print "endmodule"
        sys.stdout=console
    fobj.close()
    #--------------------------------------------------------------------------
    #基本数据的打印输出
    #--------------------------------------------------------------------------
    if presult:
        print 'Info:LUT cnt is      : '+str(len(all_lut_dict.keys()))
        print 'Info:LUT1-6 number is: '+str(lut_type_cnt)
        print 'Info:FD CNT is       : '+str(counter)+":::"+str(len(all_fd_dict))
        print 'Info:replace FD CNT  : '+str(fd_replace_cnt)
        print 'Info:Useful LUT CNT  : '+str(len(FD_din_lut_list))
        print 'Info:edited LUT CNT  : '+str(cnt_edited_lut)
        print 'Info:FD has a CE CNT : '+str(fd_ce_cnt)
        print 'Info:ce_signal CNT is: '+str(len(ce_signal_list))
    print 'Job: Full Scan insertion of  %s done\n\n' % fname
    return True

#############################################################################################
if __name__=='__main__':
    if len(sys.argv) == 1:
        print "single-file mode in ", os.getcwd()
        fname = raw_input("plz enter the file name:")
        k = int( raw_input("plz enter K:") )
        insert_scan_chain_new(fname, K = k )

    elif sys.argv[1]=='-batch': 
        print "batch mode", os.getcwd()         
        pwd = ""
        while(not os.path.exists(pwd)):
            pwd = raw_input("plz enter vm files path:")
        outpath = os.path.join(pwd, "full_using_lut")
        if not os.path.exists( outpath ):
            os.mkdir(outpath)
        K=int( raw_input('plz enter the K parameter of FPGA:K=') )
        assert (K==6 or K==4),"K not 4 or 6"

        for eachFile in os.listdir(pwd):
            if os.path.splitext(eachFile)[1] in ['.v','.vm']:
                print "Inserting scan for ", eachFile
                insert_scan_chain_new(eachFile, False, True, pwd ,outpath, K)
