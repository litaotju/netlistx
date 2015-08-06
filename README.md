# netlist_util
author :litao</br>
inst   :tju</br>
e-mail :litaotju@live.cn</br>
一个基本的Python模块库，主要的作用有两个：</br>
1 对综合出来的FPGA Verilog网表进行自动的编辑和修改，插入扫描链。该功能的顶层函数包含在 insert_scan_chain.py当中。</br>
2 对综合出来的FPGA Verilog网表识别进行信息的提取，构建s_graph以及其他的有用的电路图模型,该功能的顶层函数包含在 graph_top.py当中。</br>
</br>
整个工程的输入为；Synplify综合产生的verilog Netlist</br>
基本的测试输入存放在./test_input_netlist/目录下</br>

