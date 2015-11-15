# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 13:16:27 2015

@author: litao
@e-mail:litaotju@qq.com
@license: Free

"""
import os
import networkx as nx
import matplotlib.pylab as plt

# user-defined module
import netlistx.class_circuit as cc
from netlistx.exception    import *
from netlistx.file_util    import vm_files

from crgraph      import CloudRegGraph
from circuitgraph import get_graph

class Ballaster:
    '''
        作用：把CloudRegGraph变成一个b结构，最终返回的值应该是原图中的regs节点
        注意ballaster当中的函数都对整数型的节点的图有效
    '''
    def __init__(self, graph):
        ''' para: graph, a CloudRegGraph instance
        '''
        # 9.25 修改构造函数
        assert isinstance(graph, (CloudRegGraph, nx.DiGraph)), str(graph.__class__)
        self.graph = graph
        self.arc = graph.arcs if isinstance(graph, CloudRegGraph)\
                else {(edge[0],edge[1]): graph[edge[0]][edge[1]]['weight'] for edge in graph.edges_iter()}
        self.intgraph , self.node_mapping = self.__convert2intgraph()
    
    def __convert2intgraph(self):
        ''' 
            拓扑图只是包含了节点以及他们的连接，所以在进行基于结构的算法时候只需要
            把图转换成每一个节点是独特的整数的图就可以了,同时返回节点队列，
            用于算法找到整数边之后，get_scan_fd的查询
        '''
        graph = self.graph
        intgraph = nx.DiGraph()
        intgraph.name = graph.name + "_intgraph"
        nodes = graph.nodes()
        print "Info: intgraph edges are:"
        for edge in graph.edges_iter():
            intedge = (nodes.index(edge[0]), nodes.index(edge[1]))
            # 将FD的数量作为每一条边的权重加入到整数图中
            intgraph.add_edge(intedge[0], intedge[1],{'weight':len(self.arc[edge]),\
                                                       'label':len(self.arc[edge])})
            print "%s %d" % ( str(intedge), len(self.arc[edge]) )
        node_mapping = nodes #每一个整数对应的Cloud,存储在这个列表当中
        # TODO: for debugability, should print the info of eachNodes in nodes_mapping
        return intgraph, node_mapping
        
    def feedbackset(self):
        '''
        step1 找出给定的 cr 图的 feedback 集合,存到数据self.graph.fas 当中去
        '''
        graph = self.graph
        graph.fas = [] # 给原图增加数据属性，fas
        feedbackset_index = []
        for c in nx.simple_cycles(self.intgraph):
            print "Info: find cycle %s " % c
            if len(c) == 1: 
            #self-loop
                edge = (c[0], c[0])
            else:
                edge = (c[0], c[1])
            if not edge in feedbackset_index: # 因为edge是一个整数型元组，所以这是对的
                feedbackset_index.append(edge)
        for index in feedbackset_index:
            graph.fas.append( (self.node_mapping[index[0]], self.node_mapping[index[1]]) )
        # 只是在整数图上进行移除，所以下面的操作也只是针对整数图
        self.intgraph.remove_edges_from(feedbackset_index)  
        self.intgraph.fas = feedbackset_index
        if not feedbackset_index: print "Info: none FAS found in this graph"
        return feedbackset_index
        
    def balance(self,graph):
        '''parame: graph, a DAG its.__class__ == nx.DiGraph
           return: r,     removed edges set so makr the input graph a b-structure
        '''
        # step2 ,输入一个无环的图，对其进行balance
        # 只处理整数形式的图，每一个整数对应的节点可以在后面查到
        # 输入进来的图应该是连通的，如果存在非连通图，minimum_edge_cut就会产生问题
        assert nx.is_directed_acyclic_graph(graph),\
            "The target graph you want to banlance is not a DAG"
        r = [] # removed set
        if self.__check(graph):
            return r
        #非B-Stucture时，一直循环下去
        # BUGY: 如果cs为空呢，那么不可能有两个图返回来，这时候怎么办
        print "Cutting Graph"
        cs, g1, g2 = self.__cut(graph) 
        r = self.balance(g1) + self.balance(g2) + cs
        csl = []
        for eachEdge in cs:
            under_check_graph = graph.copy()
            under_check_graph.remove_edges_from(r)
            under_check_graph.add_edges_from(csl)
            under_check_graph.add_edge(eachEdge[0], eachEdge[1])
            if self.__check(under_check_graph):
                print "Edge: %s added back" % str(eachEdge)
                csl.append(eachEdge)
                graph.add_edge(eachEdge[0],eachEdge[1])
        for eachEdge in csl:
            r.remove(eachEdge)
        print "Removed Edge Set: %s" % str(r)
        return r

    #--------------------------------------------------------------------------------
    # 下面是直供balance算法调用的私有函数    
    def __check(self,graph):
        '''
        输入一个图G(v,A,H)来判断是否是B-structure,
        返回：True:是B-Structure，False，不是B-Structure
        '''
        # No hold register in this graph
        debug = False
        if debug: print "Procesing: checking graph for b-structure"
        if not isinstance(graph, nx.DiGraph):
            print "The graph is not a nx.DiGraph isinstance"
            raise Exception
        if not nx.is_directed_acyclic_graph(graph):
            return False
        roots = [node for node in graph.nodes_iter() if graph.in_degree()[node]==0]
        if len(roots) < 1:
            return False
        # 广度优先搜索,访问根节点，访问根节点的下一层节点， 为每一个点定Level
        # 访问一层节点的下一层节点，直到将所有的节点访问完，跳出。
        for root in roots:
            bfs_queue = [root]
            level = {root:0 }                  #记录每一个点的LEVEL的字典，初始只记录当前root
            been_levelized = []                #已经被定级的节点
            current_level = 0                  #当前的层
            if debug: print "root          :%s" % str(root)
            while(bfs_queue):
		        # 传进来的bfs_queque的层是已知的，
		        # 记录下它们的所有后继结点，并为他们定层次为n+1,同时放到待访问序列里面
                current_level +=1
                next_level_que = []
                for eachNode in bfs_queue:
                    for eachSucc in graph.successors(eachNode):
				        # 当一个节点是当前层多个节点的后继时，只加入到next_level_que一次
                        if not eachSucc in next_level_que:
                            next_level_que.append(eachSucc)
                            if debug: print "now: %s" % str(eachSucc)
                            if not level.has_key(eachSucc):
                                level[eachSucc] = current_level
                            elif level[eachSucc] ==current_level:
                                continue
                            else:
                                if debug: print "node: %s has violated the rule. %d,%d" \
							            % (str(eachSucc),level[eachSucc],current_level)
                                return False
                been_levelized += bfs_queue
                bfs_queue = next_level_que
                if debug:
                    print "been_levelized:%s " % str(been_levelized)+str(next_level_que)
                    print "root_queue    :%s " % str(next_level_que)
            if debug: print "Level: %s" % str(level)
        return True
    #--------------------------------------------------------------------------------
    
    def __cut(self, graph):
        ''' parame: 
                graph:a nx.DiGraph obj
	        return:
		        cs : edge cut set of the graph
		        g1 , g2 : subgraphs induced by cs
	
        '''
        debug = True
        assert isinstance(graph, nx.DiGraph), "Input_para.__class__  %s " % graph.__class__
        assert graph.number_of_nodes() > 1,   "Number of nodes: %d" % graph.number_of_nodes()
        if debug: print "Digraph Edges Are:\n    %s" % str(graph.edges())
        unigraph = nx.Graph(graph)           #将输入的图转为无向图
        cs = nx.minimum_edge_cut(unigraph)   #找出该无向图的minimum edge cut -> CS
        #balance函数调用cut前，graph一定是一个un-balance 结构，所以一定有CUT?
        if not cs:
            raise Exception,"Cut Set of this graph is Empty"
        #CS中的边，可能不存在于原来的有向图中，所以需要将这种边的方向颠倒
        #将所有real edge,存到RCS中
        rcs = []
        original_edges = graph.edges()
        for eachEdge in cs:
            if not eachEdge in original_edges:
                eachEdge = (eachEdge[1], eachEdge[0]) #调换方向
            rcs.append(eachEdge)
        graph.remove_edges_from(rcs)			      #在原图中移除CS
        if debug: print "Edge Cut Set RCS :\n    %s" % str(rcs)
        if debug: print "After remove RCS :\n    %s" % str(graph.edges())
    
        # 移除RCS中的边之后得到的两个Weakly Connected Subgraph
        glist = []
        for eachCntComp in nx.weakly_connected_component_subgraphs(graph):
		    #找到移除CS后的两个弱连接分量
            glist.append(eachCntComp)
            if debug:
                print "Weakly CC %d:" % len(glist)
                print "    nodes:%s" % eachCntComp.nodes() 
                print "    edges:%s" % eachCntComp.edges()
        assert len(glist) == 2
        return rcs, glist[0], glist[1]

    #--------------------------------------------------------------------------------

    def get_scan_fd(self,scans):
        '''从边来获取要扫描的D触发器
            para：r
            return: scan_fds , a list of cc.circuit_module instance
        '''
        debug = True
        scan_fds = []
        for eachEdge  in scans:
            source = self.node_mapping[eachEdge[0]]
            sink   = self.node_mapping[eachEdge[1]]
            scan_fds += self.arc[(source,sink)]
        if debug:
            print "Info: %d has to been scan " % len(scan_fds)
            #对详细的结果，扫描的FD的名字打印到 tmp/目录相应的文件下
            import sys
            log_name = "tmp\\"+self.graph.name +"_scan_fds.log"
            fobj = open(log_name,'w')
            console = sys.stdout
            sys.stdout = fobj
            print "The scan FDs are:" 
            print "\n".join([fd.name for fd in scan_fds])
            # 打印完详细的结果，将输出重定向到console上
            sys.stdout = console
            fobj.close()
        return None
# --------------------------------------------------------------------------------------

def __test_with_intgraph():
    '''使用整数图来测试Ballaster的算法
    '''
    g1 = nx.DiGraph()
    g1.add_path([0,1,2,0])
    g1.add_path([2,3,4,2])
    b1 = Ballaster(g1)
    b1.feedbackset()
    print "FAS is %s" % g1.fas

    g2 = nx.DiGraph()
    g2.add_path([1,0,5,1])
    g2.add_path([5,1,3,5])
    g2.add_path([2,1,3,2])
    g2.add_path([5,4,3,5])
    b2 = Ballaster(g2)
    b2.feedbackset()
    b2.balance(b2.intgraph)
    print "FAS is %s" % g2.fas

def __test_with_crgraph():
    '''输入一个vm文件来测试 Ballaster算法
    '''
    # 第一步：获取cr图
    g = get_graph()
    g.info()
    crgraph = CloudRegGraph(g)
    crgraph.info()

    # 第二步进行ballaster
    ballast1 = Ballaster(crgraph)
    fas = ballast1.feedbackset()
    print "Ballaster.intgraph.fas is:"
    print ballast1.intgraph.fas
    print "Ballaster intgraph info After removed FAS:"
    print nx.info(ballast1.intgraph)
    r = ballast1.balance(ballast1.intgraph)
    if not r:
        print "Info: B-structure after FAS removed.\nInfo: balance function found 0 fds "
    
    # 第三步 输出扫描D触发器，同时画出图形
    scans = r + fas
    ballast1.get_scan_fd(scans)
    plt.figure(ballast1.intgraph.name+"_after FAS")
    nx.draw(ballast1.intgraph)
    plt.show()

def __paint_intgraph(path= None):
    '''将path目录下的每一个的intgraph画出来
    '''
    if not path:
        path = raw_input("plz enter a vmfiles path:")+"\\"
    picpath = path+"pic\\"
    if not os.path.exists(picpath):
        os.mkdir(path+"pic\\")
    for eachVm in vm_files(path):
        g = get_graph(path+eachVm)
        g.info()
        crgraph = CloudRegGraph(g)
        crgraph.info()
        ballast1 = Ballaster(crgraph)
        p = ballast1.intgraph #整数图
        
        savefile = picpath+"int_"+g.name
        nx.write_dot(p, savefile+".dot")
        try:
            result = os.system("dot -Tjpg -o %s_dot.jpg %s.dot" %(savefile, savefile ))
            if result != 0:
                print "Failed to convert dot to png"
                exit(-1)
        except Exception,e:
            print e
            exit(-1)
    
if __name__ == '__main__':
    'test the ballaster'
    print "Ballaster Help:"
    print u" int: 使用内置(脚本中定义好的)的int类型图来进行测试"
    print u" cr:输入一个vm文件，然后使用ballast，输出扫描FD的结果"
    print u" pint: 输入一个目录，对所有该目录下的.v或者.vm文件进行crgraph建模，并且保存.dot图形"
    cmdlist = ["int", "cr", "pint", 'exit']
    while(1):
        cmd = raw_input("plz enter command:")
        if cmd not in cmdlist:
            print "WRONG CMD"
            continue
        if cmd =="int":
            __test_with_intgraph()
            continue
        if cmd == "cr":
            __test_with_crgraph()
            continue
        if cmd =="pint":
            __paint_intgraph()
            continue
        else: # exit
            break




    
