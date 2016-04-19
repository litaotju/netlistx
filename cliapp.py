# -*-coding: utf-8 -*- 
u'''一个基本的命令行应用类
'''
import os
import sys

__all__ = ["CliApp"]

class CliApp(object):
    '''基本的命令行程序
    '''
    #常量
    QUIT_COMMANDS = ('quit', 'exit', 'q')
    MODE_INTERACTIVE = 'interactive'
    MODE_BATCH = 'batch'
    DEFAULT_PATH = os.getcwd()
    DEFAULT_MODE = MODE_INTERACTIVE

    def __init__(self, name=None):
        self.name = "CliApp" if name == None else name
        self.call = {}  # cmd:func

        self.mode = CliApp.DEFAULT_MODE # batch or interactive
        self.path = CliApp.DEFAULT_PATH #默认路径为 os.getcwd()当前路径, 不变式：self.path一直是存在的路径
        self.current_file = ""  #当前都进来的文件。空字符串或者文件的绝对路径
        self.cmd = ""          #当前的命令
        self.opt = []          #当前的命令的选项
        self.next_call_func = self.printUsage  #下一个要调用的函数。默认打印帮助
        self.history = []       #输入过的命令历史
        
        self.addFunction('cd', self.setPath)
        self.addFunction('pwd', self.printPath)
        self.addFunction("ls", self.listPath)
        self.addFunction("help", self.printUsage)
        self.addFunction('history', self.showHistory)
        self.addFunction('setmode', self.setMode)
        self.addFunction("readvm", self.getSingleFile)
        self.addFunction("mode", lambda: sys.stdout.write(self.mode + os.linesep))
        self.addFunction("file", lambda: sys.stdout.write(self.current_file + os.linesep))
        if os.name == 'nt': 
            self.addFunction('cls', lambda: os.system("cls"))

    def setMode(self):
        u'''设置运行的模式，批处理或者单个文件的模式, i or b
        '''
        input_mode = raw_input("mode ( i for interactive and b for batch) > i/b?:") \
                                if not self.opt else self.opt[0]
        if input_mode in ['i', 'b']:
            self.mode = CliApp.MODE_BATCH if input_mode == 'b' else CliApp.MODE_INTERACTIVE
        else:
            print "Warning, did not change the mode correctly. current mode is:", self.mode

    def getCmd(self):
        u'''打印netlistx:>prompt提示，并获取命令和选项
        '''
        leaf_path = os.path.split(os.path.abspath(self.path))[-1] #当前路径的最后一级
        prompt = "[%s %s @ %s]>:"% (self.name, self.mode, leaf_path)
        args = raw_input(prompt).split()
        cmd = args[0].strip()
        #根据命令。获取下一个要运行的函数
        if cmd in self.call.keys():
            self.cmd = cmd
            self.next_call_func = self.call[self.cmd]
        elif cmd in CliApp.QUIT_COMMANDS:
            print "ByeBye"
            sys.exit(0)
        else:
            print "Cannot found commond:", args
            self.next_call_func = self.printUsage
        #如果有额外的参数，则设置额外的参数
        if len(args) > 1:
            self.opt = [opt.strip() for opt in args[1:]]
        else:
            self.opt = []
        self.history.append(str(args)[1:-1])

    def setPath(self):
        u'''设置工作路径, 如果指定目录不存在，当前目录保持不变，并打印当前绝对目录,用法: cd path
         '''
        path = raw_input("plz enter path>") if not self.opt else self.opt[0]
        #保持path的绝对路径属性
        if not os.path.isabs(path): 
            path = os.path.join(self.path, path)
        #存在则更新，不存在打印当前路径
        if os.path.exists(path):
            self.path = path
        else:
            print "Warning: invalid path."
            self.printPath()
        return
        
    def printPath(self):
        u'''显示当前绝对路径
        '''
        print "Current abs path is: ", self.path

    def listPath(self):
        u'''列出当前工作目录下的信息
        '''
        print "    ".join(os.listdir(self.path))

    def showHistory(self):
        u'''列出命令历史
        '''
        print os.linesep.join(self.history)
        
    def printUsage(self):
        u'''打印用法信息
        '''
        print "--------------------------usage----------------------------"
        print os.linesep.join(["%10.10s : %s" % (cmd, func.__doc__)\
                                  for cmd, func in self.call.iteritems()])
        print "--------------------------usage----------------------------"

    def getSingleFile(self):
        u'''预读取一个文件，设置为当前文件。并返回当前的文件名
        '''
        filename = raw_input("plz enter a filename:")  if not self.opt else self.opt[0]
        if not os.path.isabs(filename):
            filename = os.path.join(self.path, filename)
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print "Error: cannot found file: ", filename
            print "current file is: ", self.current_file
        else:
            self.current_file = filename
        return

    def addFunction(self, cmd, func):
        u'''@brief:为app添加新的 cmd-func对，添加新的功能
            @params:
                cmd, a string indicate the cmd from user
                func, a callable object for cmd
        '''
        assert callable(func), "%s is not call able" % func
        if self.call.has_key(cmd):
            override = raw_input( "Waring: all ready have a cmd%s,\
                                 do you want to override: (yes?no)" % cmd)
            if override == 'yes':
                self.call[cmd] = func
        else:
            self.call[cmd] = func

    def run(self):
        while True:
            self.getCmd()
            self.next_call_func()

if __name__ == "__main__":
    CliApp().run()
