# -*- coding:utf-8 -*- #
u'''
对于完全图来说，整个算法所需要的消耗的时间好像太长了，以及算法所发现的不平衡边，太多了。N = 4的完全图中，有36条不平衡路径。
'''
import networkx as nx

def unbalance_paths(G):
    '''
    @param: G, a nx.DiGraph obj
    @return：{}  upath2, all unbalance unbpath, 
    '''
    upath2 = []
    def is_unp(s,t):
        if s is t or G.out_degree(s) <= 1:
            return None
        paths = list(nx.all_simple_paths(G,s,t))
        if len(paths) == 1:
            return None
        for path in paths[1:]:
            if len(path)!=len(path[0]):
                return ((s,t),paths)
    for s in G.nodes_iter():
        for t in G.nodes_iter():
            upath2.append(is_unp(s,t))
    upath2 = filter(lambda x: x!= None, upath2)
    upath2 = {x[0]:x[1] for x in upath2}
    return upath2


def unbalance_paths_deprecate(G):
    '''
    @param: G, a nx.DiGraph obj
    @return：{}  upath2, all unbalance unbpath, 
        key: multi fanout node A, value: paths from A
    '''
    # 该程序不能找到所有的环，只能找到所有的不平衡路径。原因是，在搜索的时候，只搜索了所有
    # 出度大于1的节点，可以进行改进。将第一步没有搜索的点，全部搜索一遍，从而找出图中的环
    upath = {}
    upath2 = {}
    nodes = [node for node in G.nodes() if G.out_degree(node)>1]
    for s in nodes:
        upath[s] = find_upath(G, s)
        if __name__ == "__main__":
            print "Snode, Tnodes: %s %s" % ( str(s), str(upath[s]) )
        for t in upath[s]:
            assert not upath2.has_key( (s,t) )
            # TODO: s5378 memerror ni nx.all_simple_paths
            unbalance_path_st = list( nx.all_simple_paths(G, s, t) )
            if len(unbalance_path_st) >= 2:
                upath2[ (s,t) ] = unbalance_path_st
            else:
                #print "Error Only one path s:%s->t:%s, %s" %(s, t, unbalance_path_st )
                #raise AssertionError
                continue
    return upath2
    
def find_upath(G, s):
    '''@param: G, an DiGraph obj
             : s, a node in G
        @return: reconvergent nodes in from s.
    '''
    if __name__ == "__main__":
        print "Searching node: %s" % s
    time = 0
    depth = {}
    depth[s] = [0]
    reconvergent_nodes = []
    
    bfs_list = G.succ[s].keys()
    while(len(bfs_list) != 0 ):
        time += 1
        next_list = []
        if __name__ == "__main__":
            print "bfs_list: ",
            print bfs_list
        # 传递进来的一定是没有经过访问的标定深度的节点
        # 所以为每一个标定一下深度
        for node in bfs_list:
            if node is s or node == s:
                continue
            assert not depth.has_key(node) ,"Node: %s" % str(node)
            depth[node] = (time)
            #print "Node:%s depth:%d" % ( str(node), time )
                
        # 找出下一级的节点，（本级没有包含，前级也没有包含的节点）
        # 如果本级包含或者前级包含了，那么该节点一定是重汇聚节点
        for node in bfs_list:
            if node is s or node == s:
                continue
            for next_level_node in G.succ[node].keys():
                if next_level_node is node:
                    #print "Finding:self-loop %s" % node
                    continue
                if depth.has_key(next_level_node):
                    if not (next_level_node in reconvergent_nodes):
                        reconvergent_nodes.append(next_level_node)
                    continue
                elif next_level_node not in next_list:
                    next_list.append(next_level_node)
                else:
                    continue
        bfs_list = next_list 
    return reconvergent_nodes

def __stat_complete():
    '''统计节点数目为1-10的完全图中的不平衡路径的个数
    '''
    number = []
    for i in range (1, 11):
        G = nx.DiGraph(nx.complete_graph(i))
        print G.number_of_edges() 
        u = unbalance_paths(G)
        j = 0
        for key, val in u.items():
            j += len(val)
        number.append(j)
    return numbers
    
    
def __draw_complete(i):
    '''@param: i, nodes number of complete complete_graph
     @brief: just draw a graph 
    '''
    import matplotlib.pylab as plt
    G = nx.DiGraph(nx.complete_graph(i))
    plt.figure("Complete DiGraph %d" % i)
    nx.draw(G)
    plt.show()	
    return None
    
if __name__ == "__main__":
    G = nx.DiGraph()
    edges = [
		('a', 'b'),('a', 'c'),('a','d'),('c','d'),
		('b','c'),('b','d'),
		('c', 'e'),('d','e'),
		('e','f'),('a','a'),
	]
    edges2 = [('a','b'), ('b','c'), ('c','a'), ('f','f')]
    edges3 = [('a','b'),('b','a'),('b','c'),('c','a')]
    edges4 = [('a','b'),("a",'c'),('a','a')]
    G.add_edges_from( edges+ edges2)
    u = unbalance_paths(G)
    cycles = []
    print "Un-balance Paths:"
    for key , val in u.items():
        for path in val:
            if path[0] is path[-1]:
                continue
            else:
                print "%s %s " % (str(key), str(path))


