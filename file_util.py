# -*- coding: utf-8 -*- #
u'''本模块主要处理和网表文件查找，以及输出重定向的函数
'''
import os
import sys
import functools

def vm_files(path):
    '''返回特定目录下的全部vm或者v file
    '''
    for vmfile in os.listdir(path):
        if os.path.splitext(vmfile)[1] in ['.v', '.vm']:
            yield vmfile

def vm_files2(path):
    for vmfile in os.listdir(path):
        if os.path.splitext(vmfile)[1] in ['.v', '.vm']:
            yield os.path.join(path, vmfile)

class StdOutRedirect(object):
    '''输出重定向到文件
    '''
    def __init__(self, filename, mode=None):
        if mode is None or mode not in ['w', 'a']:
            self.out = open(filename, 'w')
        else:
            self.out = open(filename, mode)
        self.console = sys.stdout

    def __enter__(self):
        self.console = sys.stdout
        sys.stdout = self.out

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.console
        self.out.close()

def print_to(filename, mode=None):
    u'''重定向一个函数的输出到filename, 默认以 w 的形式'''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            with StdOutRedirect(filename, mode): #default mode is "w"
                result = func(*args, **kwds)
            return result
        return wrapper
    return decorator
