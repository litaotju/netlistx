# netlistx 包

author :litao</br>
inst   :tju</br>
e-mail :[李涛的邮箱](litaotju@live.cn)</br>
copyright: free copy and use

##简要介绍
netlistx一个Python包，主要的功能有：

* 读取并解析网表文件, 生成内部python对象.
* 对综合出来的FPGA Verilog网表进行自动编辑和修改，插入扫描链.
* 从网表构建CircuitGraph.
* 从基本的CircuitGraph构建更抽象的电路图，比如CloudRegGraph，SGraph.

##使用方法
* 包的顶层文件夹名称不能改动,必须是 **netlistx**
* 将包所在的目录加入到PYTHONPATH环境变量中。
* 安装requirements.txt中的依赖.
* partialScan功能需要主机上存在Matlab,且可以直接通过命令行调用.

##架构

    netlistx \文件名必须叫这个

        __init__.py
        exception.py     \自定义异常类型类s
        file_util.py     \读取vm文件,输入输出重定向
        class_circuit.py \所有与电路相关的python类s
        netlist.py       \Netlist类
        netlist_rules.py \规则检查
        netlist_util.py  \网表的其他可用函数

        cell_construct \单元库构建
            construct_scan_lib.py \由xilinx unisim.v 生成扫描所需的基本单元 SCAN_FD*
            faultlib.py \生成故障注入单元FIE

        graph \图的生成
            __init__.py
            ballast.py      \BALLAST方法的实现
            circuitgraph.py \CircuitGraph类
            cloudgraph.py   \CloudRegGraph类
            crgraph.py      \The old CloudRegGraph类
            main.py         \与图相关的生成与验证,可以直接执行此文件

        itrans \iscas89门级网表翻译器.
            itrans.py       \可执行,用来读取同目录下的iscas .v网表
            Primitives.py   \Dff和Combi类定义

        parser \vm文件解析器 parser
            __init__.py
            lex.py             \ply lex
            yacc.py            \ply yacc
            netlist_lexer.py   \网表词法分析器
            netlist_parser.py  \网表解析器.生成class_circuit中的定义的各种类型对象.
            parsetab.py        \自动生成的,不要修改

        prototype \函数原型测试.未验证功能正确的函数暂时存放在此目录
            __init__.py
            balance.py
            check.py
            cut.py
            fas.py
            unbpath.py

        scan \扫描插入子包.每一个文件均可单独执行
            __init__.py
            fullReplace.py
            fullUsingLut.py
            partialBallast.py
            partialOpt.py
            partialOptLinear.py
            partialFusion.py
            testbenchGenerate.py

		unittest \#单元测试文件夹
        test \测试文件目录.




