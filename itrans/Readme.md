# itrans is short for "IscasTranslator"

本目录是为了方便将iscas89 基准电路门级网表翻译成crgraph的图形式，验证Ballast实验的准确性。
经过测试本程序能正常工作无误。

与Fujiwara文中结果表格逐项进行比对：

将不同项目的对比列举如下：
circuit   Fujiwara  Our
s5378     124       162
s9234.a   193       201
s13207.a  441       471+(图的规模比较大，没有算清楚)
s15850.a  483       498
s38417    1255      图太大没有算清楚
s38454.a  1419      1421
s35932    1728      1728 (退化成全扫描)
