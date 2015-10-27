# netlistx 包

author :litao</br>
inst   :tju</br>
e-mail :litaotju@live.cn</br>

##简要介绍
一个基本的Python包，主要的作用有：

1 对综合出来的FPGA Verilog网表进行自动的编辑和修改，插入扫描链。该功能的顶层函数包含在 insert_scan_chain.py当中。  
2 对综合出来的FPGA Verilog网表识别进行信息的提取，构建CircuitGraph以及其他的有用的电路图模型，主要的类定义在circuitgraph.py当中。  
3 从基本的CircuitGraph构建更抽象的电路图，比如CloudRegGraph，SGraph，然后对不同的图模型进行操作，找出其中的重要节点  


整个工程的输入为；Synplify综合产生的verilog Netlist  
基本的测试输入存放在./test/目录下  
所有的单元测试放在 ./unittest/目录下  

##使用方法
将包所在的目录加入到 PYTHONPATH环境变量中。

##架构

