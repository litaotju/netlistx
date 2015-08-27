# netlist_util
author :litao</br>
inst   :tju</br>
e-mail :litaotju@live.cn</br>
一个基本的Python模块库，主要的作用有：</br>
1 对综合出来的FPGA Verilog网表进行自动的编辑和修改，插入扫描链。该功能的顶层函数包含在 insert_scan_chain.py当中。</br>
2 对综合出来的FPGA Verilog网表识别进行信息的提取，构建CircuitGraph以及其他的有用的电路图模型，主要的类定义在circuitgraph.py当中。</br>
3 从基本的CircuitGraph构建更抽象的电路图，比如CloudRegGraph，SGraph，然后对不同的图模型进行操作，找出其中的重要节点
</br>
整个工程的输入为；Synplify综合产生的verilog Netlist</br>
基本的测试输入存放在./test/目录下
每一个图模型的测试和验证放在*test目录下</br>

