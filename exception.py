# -*- coding: utf-8 -*-


class CircuitGraphError(Exception):
    def __init__(self, msg = ""):
        Exception.__init__(self, msg)


class CrgraphError(Exception):
    ''''''
    
class CrgraphRuleError(CrgraphError):
    '''CrGraph图规则检查时候的Exception '''
    pass


class BallastError(Exception):
    ""
    pass


class ScanchainError(Exception):
    pass


#和网表操纵相关的异常
class NetlistError(Exception):
    def __init__(self,msg = ''):
        Exception.__init__(self, msg)
        
class RedeclarationError(NetlistError):
    def __init__(self, msg = ''):
        NetlistError.__init__(self, msg)

class FormatError(NetlistError):
    def __init__(self, msg = ''):
        NetlistError.__init__(self, msg)