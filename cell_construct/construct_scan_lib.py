# -*- coding: utf-8 -*- #

'--this script is for verilog scan_cell lib construct--'

import os
import re

for root,dirs,files in os.walk(os.getcwd()):
    for file_name in files: 
        print file_name
    
# 读取当前目录下的\FD_SRC目录里面的verilog文件
for fdverilog in os.listdir(os.getcwd()+"\FD_SRC"):
    

fobj_scan_cell=open('scan_cells.v','w')
in_out_del='''\
    input SCAN_EN;
    input SCAN_IN;
    output SCAN_OUT;
'''
counter=0
all=[]
print len(files)
while counter<len(files)-2: #the last 2 file is scan_cells.v and sth.py
    fobj_tfi=open(files[counter],'r')
    fobj_v  =open(files[counter+1],'r')
    for eachLine in fobj_v:
        module_del    =re.match('^\s*module',eachLine)
        in_output_line=re.match('(^\s*input)|(^\s*output)',eachLine)
        endmodule_del =re.match('^\s*endmodule',eachLine)
        if module_del is not None:
            eachLine=eachLine[0:7]+'SCAN_'+eachLine[7:]
            eachLine=eachLine[:-3]+',SCAN_EN,SCAN_IN,SCAN_OUT'+eachLine[-3:]
            print eachLine
            print in_out_del
            all.append(eachLine)
            all.append(in_out_del)
        elif in_output_line is not None:
            print eachLine
            all.append(eachLine)            
        elif endmodule_del is not None:
            for eachLine2 in fobj_tfi:
                if re.match('^\s*\.D\(D\)\,',eachLine2) is not None:
                    eachLine2='    .D(SCAN_EN?SCAN_IN:D),'
                elif re.match('^\s*\.D\(D\)',eachLine2) is not None:
                    eachLine2='    .D(SCAN_EN?SCAN_IN:D)'
                elif re.match('^\s*\.CE\(CE\),',eachLine2) is not None:
                    eachLine2='    .CE(SCAN_EN?1\'b1:CE),'
                print eachLine2
                all.append(eachLine2)
            eachLine='assign SCAN_OUT=Q;\n'+eachLine
            all.append(eachLine)
            print eachLine
        else:
            continue
    fobj_tfi.close()
    fobj_v.close()
    counter=counter+2
for x in all:
    fobj_scan_cell.writelines(x)
fobj_scan_cell.close()
