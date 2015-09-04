# -*- coding: utf-8 -*-
import networkx as nx
import copy

def check(graph):
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

#-------------------------------------------------------------------------------------

def __test_check():
    # False
    g1 = nx.DiGraph()
    g1.add_path([0,0])
    assert (not check(g1))
    # True
    g2 =nx.DiGraph()
    g2.add_path([0,1,2,3,5])
    g2.add_path([3,4])
    assert(check(g2))
    print "g2 %s"% str(check(g2))
    # True
    g3 = nx.DiGraph()
    g3.add_edges_from([(1,2),(2,3),(0,3)])
    assert(check(g3))
    print "g3 %s"% str(check(g3))
    # True
    g4 = nx.DiGraph()
    g4.add_edges_from([(0,1),(0,2),(1,3),(1,4),(2,3),(2,4)])
    assert(check(g4))
    print "g4 %s" % str(check(g4))
    # False
    g5 = nx.DiGraph()
    g5.add_edges_from([(0,2),(0,3),(0,4),(1,2),(1,3),(2,5),(2,6)])
    g5.add_edges_from([(3,4),(3,5),(3,6),(4,8),(4,9),(5,8),(5,4),(6,7),(6,8)])
    print "g5 %s" % str(check(g5))
    assert(not check(g5))
	# True 1989 Ballast文章Figure6.b
    g6 = nx.DiGraph()
    g6.add_edges_from([(0,1),(2,3),(1,3),(1,4),(4,5),(3,5)])
    print "g6 %s" % str(check(g6))
    assert (check(g6))
    
if __name__ == '__main__':
    __test_check()
