# -*-coding:utf-8 -*- #

dffkeyword = 'dff'
primtypes = set([ 'dff', 'not', 'nand', 'nor', 'and', 'or'])
class Combi:
    def __init__(self, cellref, name, output, inputs):
        self.cellref = cellref
        self.name = name 
        self.output = output
        self.inputs = inputs 
    
    def __str__(self):
        return "%s %s(%s,%s);" \
            %(self.cellref, self.name, self.output, ",".join(self.inputs) )

class Dff:
    cellref = dffkeyword
    def __init__(self, name, C, Q, D):
        self.name = name
        self.c = C
        self.q = Q
        self.d = D
        self.input = self.d
        self.output = self.q

    def __str(self):
        return "%s %s(%s,%s,%s);" %(self.cellref, self.name, self.c, self.q, self.d)