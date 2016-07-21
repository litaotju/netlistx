# -*- coding: utf-8 -*-
u'''本模块提供了一个获取扫描触发器的App框架ScanApp类，该类只能被继承，不能直接例化。
'''
import time
import os

__all__ = ["ScanApp"]

import netlistx.circuit as cc
from netlistx.parser.netlist_parser import vm_parse
from netlistx.cliapp import CliApp
from netlistx.netlist import Netlist

class UnimplementedError(Exception):
    pass


class ScanApp(CliApp):
    u'''获取扫描触发器的各种方法的基类
    '''

    def __init__(self, name):
        super(ScanApp, self).__init__(name)
        self.circuit_name = "" #当前处理的电路的名称
        self.netlist = None #当前处理的网表对象
        self.scan_fds = [] #当前处理的电路的扫描触发器
        self.fds = []      #当前处理的电路的触发器

        self.stats_items = [] #统计数据三元组， （名称，格式，数据）

    def _process(self, vm):
        u'''覆写CliApp父类的该方法'''
        #当前处理的电路的名称 = vm文件的文件名
        self.circuit_name = os.path.splitext(os.path.basename(vm))[0]
        #设置输出路径为App的名称
        self.setOpath(self.name)
        self.stats_items = []
        #解析网表。将网表对象赋值为 self.netlist
        self.parse_netlist(vm)

        #从网表获得触发器，保存到self.scan_fds中
        self._get_scan_fds()
       
        #获取触发器之后的其他动作，默认是什么都不做。作为hook留给子类
        self.after_get_scan_fds()

        #保存同一个APP的所有信息到csv文件
        self.save_info_item2csv()
        self.write_scan_fds()

    def _get_scan_fds(self):
        u'''从vm文件得到所有的触发器和扫描触发器'''
        #self.fds = ...
        #self.scan_fds = ...
        raise UnimplementedError

    def save_info_item2csv(self):
        u'保存一条信息item到 records 文件下'
        #保存的文件名
        records = "%s_records.csv" % self.name
        SEP = ','
        
        #电路中原本的LUT
        number_of_luts = len(filter(lambda x: cc.isLUT(x), self.netlist.primitives))
        
        #扫描后总的LUT = 原来的LUT+扫描带来的消耗
        number_of_luts_after_scan = number_of_luts + sum((fd.input_count() for fd in self.scan_fds))
        
        # 需要记录的数据内容， 每一个元素为一个三元组， （项名称，格式化字符串，数据）。可以按需要更改
        self.stats_items += [
            ('circuit', "%s", self.circuit_name),
            ('#FD', "%d", len(self.fds)),
            ("#LUT", "%d", number_of_luts),
            ("#SCAN_FD", '%d', len(self.scan_fds)),
            ("#LUT_AFTER_SCAN", '%d', number_of_luts_after_scan),
            ('#TIMESTAMPE', '%s', time.time()),
            ('#CTIME', '%s', time.ctime())
            ]
        #表项目
        cols = SEP.join([item[0] for item in self.stats_items])
        #格式
        item_format = SEP.join([item[1] for item in self.stats_items])
        #数据
        item_data = tuple([item[2] for item in self.stats_items])

        records = os.path.join(self.opath, records)
        if not os.path.exists(records):
            with open(records, 'w') as fobj:
                fobj.write(cols + os.linesep)
        with open(records, 'a') as fobj:
            #格式化字符串
            formated_item = item_format % item_data
            fobj.write(formated_item + os.linesep)

    def write_scan_fds(self):
        u'''保存每一个电路的信息到扫描触发器的信息到output_file文件中'''
        output_file = os.path.join(self.opath, self.circuit_name+ "_ScanFDs.txt")
        with open(output_file, 'w') as out:
            for fd in self.scan_fds:
                try:
                    out.write("%s %s\n " % (fd.cellref, fd.name))
                except AttributeError:
                    out.write("%s %s\n " % (fd.port_type, fd.name))
            out.write("#FD: %d" % len(self.fds))
            out.write("#SCAN_FD: %d" % len(self.scan_fds))

    def after_get_scan_fds(self):
        u'''This is a hook for subclass to do something after _get_scan_fds'''
        pass

    def parse_netlist(self, vm):
        u'''解析网表
        '''
        info = vm_parse(vm)
        self.netlist = Netlist(info)


class FullScanApp(ScanApp):
    u'''Just for demonstrate how ScanApp class be used
    '''
    def __init__(self):
        super(FullScanApp, self).__init__(name="FullScan")

    def _get_scan_fds(self):
        self.fds = filter(lambda x: cc.isDff(x), self.netlist.primitives)
        self.scan_fds = self.fds

if __name__ == "__main__":
    FullScanApp().run()