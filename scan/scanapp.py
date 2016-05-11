# -*- coding: utf-8 -*-
u'''本模块提供了一个获取扫描触发器的App框架ScanApp类，该类只能被继承，不能直接例化。
'''
import time
import os

__all__ = ["ScanApp"]

from netlistx.cliapp import CliApp

class UnimplementedError(Exception):
    pass

class ScanApp(CliApp):
    u'''获取扫描触发器的各种方法的基类
    '''
    def __init__(self, name):
        super(ScanApp, self).__init__(name)
        self.circuit_name = "" #当前处理的电路的名称
        self.scan_fds = [] #当前处理的电路的扫描触发器个数
        self.fds = []  #当前处理的电路的触发器个数

    def _process(self, vm):
        u'''覆写CliApp父类的该方法'''
        #当前处理的电路的名称 = vm文件的文件名
        self.circuit_name = os.path.splitext(os.path.basename(vm))[0]
        #设置输出路径为App的名称
        self.setOpath(self.name)
        
        #从网表获得触发器，保存到self.scan_fds中
        self._get_scan_fds(vm)
        self.save_info_item2csv()
        self.write_scan_fds()

    def _get_scan_fds(self, vm):
        u'''从vm文件得到所有的触发器和扫描触发器'''
        #self.fds = ...
        #self.scan_fds = ...
        raise UnimplementedError

    def save_info_item2csv(self):
        u'保存一条信息item到 records 文件下'
        self.records = "%s_records.csv" % self.name
        self.cols = ["circuit", "#FD", "#SCAN_FD", "#TIMESTAMPE", "#CTIME"]
        self.format = "%s, %d, %d, %s, %s"
        item = self.format % (self.circuit_name, len(self.fds), \
                                len(self.scan_fds), time.time(), time.ctime())
        records = os.path.join(self.opath, self.records)
        if not os.path.exists(records):
            with open(records, 'w') as fobj:
                fobj.write(",".join(self.cols)+os.linesep)
        with open(records, 'a') as fobj:
            fobj.write(item + os.linesep)

    def write_scan_fds(self):
        u'''保存扫描触发器的信息到output_file文件中'''
        output_file = os.path.join(self.opath, self.circuit_name+ "_ScanFDs.txt")
        with open(output_file, 'w') as out:
            for fd in self.scan_fds:
                try:
                    out.write("%s %s\n " % (fd.cellref, fd.name))
                except AttributeError:
                    out.write("%s %s\n " % (fd.port_type, fd.name))
            out.write("#FD: %d" % len(self.fds))
            out.write("#SCAN_FD: %d" % len(self.scan_fds))
