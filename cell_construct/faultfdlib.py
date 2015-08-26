# -*- coding:utf-8 -*- #
import re
import os


class FIElementer:
    '''构建FIE的类，负责识别FD LIB 以及构建相应的 instrumented FD
    '''
    MODULE_PREFIX = 'SCAN_'    
    INOUTDEL = {
        'SCAN_EN':'input',
        'SCAN_IN':'input',
        'SCAN_OUT':'output'
    }
    PORT_ADDED = ''   # 要在顶层括号内打印的端口字符串
    INOUT_ADDED = ''  # 要在端口声明区打印的端口字符串
    
    def __init__(self, writeobj):
        self.fobj = writeobj
        for eachport , portattr in self.INOUTDEL.items():
            self.PORT_ADDED += (","+eachport)
            self.INOUT_ADDED += (portattr+"  "+ eachport +";\n")
            
    def _files_(self, ext1='v', ext2 = 'tfi'):
        '返回当前文件夹下的\FD_SRC文件夹下的v和tfi文件'
        fd_src = os.getcwd()+"\FD_SRC\\"
        print fd_src
        for filename in os.listdir(fd_src):
            f1 = os.path.splitext(filename)
            if  f1[1]== ext1:
                for filename2 in os.listdir(fd_src):
                    if os.path.splitext(filename2)[1] == ext2 and \
                        os.path.splitext(filename2)[0] == f1[0]:
                            print filename, filename2
                            yield filename,filename2
                    
    def libfuck(self):
        all = []
        for file1,file2 in self._files_():
            fobj1 = open(file1) # verilog fobj
            fobj2 = open(file2) # tfi fobj
            for eachLine in fobj1:
                module_del    = re.match('^\s*module',eachLine)
                in_output_line = re.match('(^\s*input)|(^\s*output)',eachLine)
                endmodule_del = re.match('^\s*endmodule',eachLine)
                
                if module_del is not None:
                    # rename the module name with a prefix                    
                    eachLine=eachLine[0:7] + self.MODULE_PREFIX + eachLine[7:]
                    # add the port decl in module declearation 
                    eachLine=eachLine[:-3]+ self.PORT_ADDED +eachLine[-3:]
                    # append the modified module decleration and ports decl
                    all.append(eachLine)
                    all.append(self.INOUTDEL)
                elif in_output_line is not None:
                    all.append(eachLine)
                    
                elif endmodule_del is not None:
                    for eachLine2 in fobj2:
                        ddecl = re.match('^\s*\.D\((D)\),?',eachLine2)
                        dreplace = "SCAN_EN?SCAN_IN:D"
                        if  ddecl is not None:
                            eachLine2 = re.sub(ddecl.group(),dreplace,eachLine2)
                        elif re.match('^\s*\.CE\(CE\),',eachLine2) is not None:
                            eachLine2='    .CE(SCAN_EN?1\'b1:CE),'
                        all.append(eachLine2)
                    eachLine='assign SCAN_OUT=Q;\n'+eachLine
                    all.append(eachLine)
        print all
        self.fobj.writelines(all)

if __name__ == '__main__':
    writefile = open('test.v','w')
    inst1 = FIElementer(writefile)
    inst1.libfuck()
    writefile.close()
    
    
    
