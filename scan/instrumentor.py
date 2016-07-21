# coding:utf-8
import re

import netlistx.circuit as cc
from netlistx.netlist import Netlist


class Instrumentor(object):
    """本类负责插入扫描链所需要的所有额外信号和顶层端口"""
    # 几个扫描信号的名称
    SCAN_IN_PORT = "SCAN_IN_PORT"
    SCAN_OUT_PORT = "SCAN_OUT_PORT"
    SCAN_EN_PORT = "SCAN_EN_PORT"
    SCAN_IN_SIGNAL = 'scan_in'
    SCAN_OUT_SIGNAL = 'scan_out'
    
    # 扫描触发器的前缀
    SCAN_FD_SUFFIX = "SCAN_"

    def __init__(self, netlist, sff_number):
        u"""
            @brief: 插入扫描的所需的信号和端口等
            @params: netlist, an instance of netlist class
                     sff_number , the number of sffs needed to be scanned
        """
        assert isinstance(netlist, Netlist)
        self.netlist = netlist
        self.sff_number = sff_number

    def insert_scan(self):
        self._insert_scan_port()
        self._insert_scan_wire()
        self._insert_scan_assign()
        self.edit_primitives()

    def _insert_scan_wire(self):
        u"插入扫描的两个信号 scan_in[0:n-1]和 scan_out[0:n-1]"
        scan_ins = cc.Signal(name=self.SCAN_IN_SIGNAL,
                             vector="[%d:%d]" % (0, self.sff_number - 1))
        scan_outs = cc.Signal(name=self.SCAN_OUT_SIGNAL,
                              vector="[%d:%d]" % (0, self.sff_number - 1))
        self.netlist.insert_wire(scan_ins)
        self.netlist.insert_wire(scan_outs)

    def _insert_scan_port(self):
        u"插入扫描的顶层端口，SCAN_IN_PORT, SCAN_OUT_PORT, SCAN_EN_PORT"
        scan_in_wire = cc.Signal(name=self.SCAN_IN_PORT)
        scan_out_wire = cc.Signal(name=self.SCAN_OUT_PORT)
        scan_en_wire = cc.Signal(name=self.SCAN_EN_PORT)

        scan_in_port = cc.Port(
            self.SCAN_IN_PORT, cc.Port.PORT_TYPE_INPUT, scan_in_wire)
        scan_out_port = cc.Port(
            self.SCAN_OUT_PORT, cc.Port.PORT_TYPE_OUTPUT, scan_out_wire)
        scan_en_port = cc.Port(
            self.SCAN_EN_PORT, cc.Port.PORT_TYPE_INPUT, scan_en_wire)

        self.netlist.insert_wire(scan_in_wire)
        self.netlist.insert_wire(scan_out_wire)
        self.netlist.insert_wire(scan_en_wire)

        self.netlist.insert_port(scan_in_port)
        self.netlist.insert_port(scan_out_port)
        self.netlist.insert_port(scan_en_port)

    def _insert_scan_assign(self):
        u"插入扫描的ASSIGN"
        scan_in_wire = cc.Signal(name=self.SCAN_IN_PORT)
        scan_in_0 = cc.Signal(name=self.SCAN_IN_SIGNAL, vector="[0]")
        self.netlist.insert_assign(scan_in_0, scan_in_wire)

        scan_out_wire = cc.Signal(name=self.SCAN_OUT_PORT)
        scan_out_last = cc.Signal(
            name=self.SCAN_OUT_SIGNAL, vector="[%d]" % (self.sff_number - 1))
        self.netlist.insert_assign(scan_out_wire, scan_out_last)

        ## scan_in[1:n-1] = scan_out[0:n-2]
        if self.sff_number > 1:
            scan_in_1_last = cc.Signal(
                name=self.SCAN_IN_SIGNAL, vector="[1:%d]" % (self.sff_number - 1))
            scan_out_0_last2 = cc.Signal(
                name=self.SCAN_OUT_SIGNAL, vector="[0:%d]" % (self.sff_number - 2))
            self.netlist.insert_assign(scan_in_1_last, scan_out_0_last2)


    def _replace_fd_with_scan_fd(self, fd, index):
        u'''@breif:将FD*替换为 SCAN_FD*, 并且增加三个和扫描有关的端口.
            @params: fd, an instance of cc.CircuirModule, and cc.idDff(fd) is true
                     index, a int to denote the location of this FD in the scan chain
        '''
        assert cc.isDff(fd)
        fd.cellref = self.SCAN_FD_SUFFIX + fd.cellref
        scan_in_signal = cc.Signal(name=self.SCAN_IN_SIGNAL, vector="[%d]" % index)
        scan_en_signal = cc.Signal(name=self.SCAN_EN_PORT)
        scan_out_signal = cc.Signal(name=self.SCAN_OUT_SIGNAL, vector="[%d]" % index)
        SCAN_IN = cc.Port('SCAN_IN', cc.Port.PORT_TYPE_INPUT, scan_in_signal)
        SCAN_EN = cc.Port('SCAN_EN', cc.Port.PORT_TYPE_INPUT, scan_en_signal)
        SCAN_OUT = cc.Port('SCAN_OUT', cc.Port.PORT_TYPE_OUTPUT, scan_out_signal)
        fd.port_list.insert(0, SCAN_OUT)
        fd.port_list.insert(0, SCAN_EN)
        fd.port_list.insert(0, SCAN_IN)


    def _fusion_lut_with_mux(self, lut, index):
        u'''@brief:将lut和mux进行逻辑混合, 插入扫描逻辑.
                    In = scan_in+str(index)
                    I(n+1) = scan_en
                    计算新的init_value
            @param: lut , a cc.CircuitModule instance 
                    index,  a int to denote the location of this LUT in the scan chain
            @return: None
        '''
        assert cc.isLUT(lut)
        input_num = lut.input_count()
        assert input_num == int(lut.cellref[3])
        assert lut.param_list is not None and len(lut.param_list) == 1

        scan_in = cc.port("I" + str(input_num), 'input',
                          cc.signal(name="scan_in" + str(index)))
        scan_en = cc.port('I' + str(input_num + 1), 'input',
                          cc.signal(name="scan_en"))
        lut.port_list.insert(-1, scan_in)
        lut.port_list.insert(-1, scan_en)

        old_init = lut.param_list[0].value
        init_legal = re.match(r'(\d+)\'[hb]([0-9A-F]+)', old_init)
        assert init_legal is not None
        assert int(init_legal.groups()[0]) == 2**input_num
        if input_num == 1:
            assert  init_legal.groups()[0] == '2' and init_legal.groups()[1] == "1",\
                "Error:find LUT1 .INIT !=2'h1 %s, is %s" % (
                    lut.name, lut.param_list[0].value)
            NEW_INIT = "8'hC5"
        else:
            NEW_INIT = str(2**(input_num + 2)) + '\'h' + 'F' * int(2**(input_num - 2)) \
                + '0' * int(2**(input_num - 2)) + (init_legal.groups()[1]) * 2
        lut.param_list[0].edit_param('INIT', NEW_INIT)
        lut.cellref = re.sub(
            'LUT[1-4]', ('LUT' + str(input_num + 2)), lut.cellref)
        assert lut.input_count() == input_num + 2

    def edit_primitives(self):
        u"编辑原语，插入扫描功能。子类决定是替换，还是Logic Fusion"
        raise NotImplementedError

class FullReplaceInstrumentor(Instrumentor):
    """全扫描插入扫描链的方法"""

    def __init__(self, netlist, scan_fds):
        sff_numbers = len(scan_fds)
        self.scan_fds = scan_fds
        super(FullReplaceInstrumentor, self).__init__(netlist, sff_numbers)

    def edit_primitives(self):
        u"直接替换每一个D触发器的原语"
        for index, fd in enumerate(self.scan_fds):
            self._replace_fd_with_scan_fd(fd, index)


class FusionInstrumentor(Instrumentor):
    """逻辑混合插入扫描链的方法"""
    K_LUT = 6

    def __init__(self, netlist, replace_dffs, fusion_pairs, K):
        sff_number = len(replace_dffs) + len(fusion_pairs)
        super(FusionInstrumentor, self).__init__(netlist, sff_number)
        self.K_LUT = K
        self.replce_dffs = replace_dffs
        self.fusion_pairs = fusion_pairs

    def edit_primitives(self):
        cnt = 0
        for fd in self.replce_dffs:
            # 使用原语替换LUT
            self._replace_fd_with_scan_fd(fd, cnt)
            cnt += 1

        for fd, lut in self.fusion_pairs:
            # 修改LUT
            self._fusion_lut_with_mux(lut, cnt)
            fd_q_port_wire = filter(lambda x: x.port_name == "Q", fd.port_list)[0]
            scan_out_wire = cc.Signal(name=self.SCAN_OUT_PORT, vector="[{}]".format(cnt))
            # 将 scan_out[i]连接到 fd的Q端口上
            self.netlist.insert_assign(scan_out_wire, fd_q_port_wire)
            cnt += 1