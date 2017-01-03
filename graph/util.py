# -*- coding:utf-8 -*-

import os
import networkx as nx

if nx.__version__ >= 1.11:
    from networkx.drawing.nx_pydot import write_dot as write_dot
else:
    import networkx.write_dot as write_dot

class WriteDotBeforeAfter(object):
    u'''write dot before and after action
    '''

    def __init__(self, opath, action, graph):
        u'''
            @params:
                opath: 输出路径
                action: 动作名称
                graph:要保存的图
        '''
        assert isinstance(graph, nx.Graph)
        action = str(action)
        self.before = os.path.join(opath, "before-" + action)
        self.after = os.path.join(opath, "after-" + action)
        for d in (self.before, self.after):
            if not os.path.exists(d):
                os.makedirs(d)
        self.graph = graph

    def __enter__(self):
        u'''进入context保存图的信息到dot
        '''
        try:
            write_dot(self.graph, os.path.join(
                self.before, self.graph.name + ".dot"))
        except Exception, e:
            print e

    def __exit__(self, exc_type, exc_value, traceback):
        u'''退出context保存图的信息到dot
        '''
        try:
            write_dot(self.graph, os.path.join(
                self.after, self.graph.name + ".dot"))
        except Exception, e:
            print e