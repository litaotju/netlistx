# -*- coding: utf-8 -*- #

import os
import sys

def vm_files(dir):
    '''返回特定目录下的全部vm或者v file
    '''
    for eachFile in os.listdir(dir):
        if os.path.splitext(eachFile)[1] in ['.v','.vm']:
            yield eachFile

def vm_files2(dir):
    for eachFile in os.listdir(dir):
        if os.path.splitext(eachFile)[1] in ['.v','.vm']:
            yield os.path.join( dir, eachFile)

class StdOutRedirect:
    '''输出重定向到文件
    '''
    def __init__(self, filename):
        self.out = open(filename, 'w')
        self.console = sys.stdout

    def __enter__(self):
        self.console = sys.stdout
        sys.stdout = self.out

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.console
        self.out.close()