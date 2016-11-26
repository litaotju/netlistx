# -*- coding:utf-8 -*- #
import networkx as nx
import netlistx.circuit as cc

def all_simple_paths(G, source, target, cutoff=None):
    """Generate all simple paths in the graph G from source to target.
    all_shortest_paths, shortest_path
    """
    if source not in G:
        raise nx.NetworkXError('source node %s not in graph'%source)
    if target not in G:
        raise nx.NetworkXError('target node %s not in graph'%target)
    if cutoff is None:
        cutoff = len(G)-1
    return _all_simple_paths_graph(G, source, target, cutoff=cutoff)

## What is the complexity of this algorithm


#TODO: 确定深度
def _all_simple_paths_graph(G, source, target, cutoff=None):
    if cutoff < 1:
        return
    visited = [source]
    stack = [iter(G[source])]
    depth = 0
    while stack:
        depth += 1
        children = stack[-1]
        child = next(children, None)
        if child is None:
            stack.pop()
            visited.pop()
        elif len(visited) < cutoff:
            if child == target:
                yield visited + [target]
            elif child not in visited:
                visited.append(child)
                stack.append(iter(G[child]))
        else: #len(visited) == cutoff:
            if child == target or target in children:
                yield visited + [target]
            stack.pop()
            visited.pop()
    #print "depth, ", depth

def unbalance_paths(G):
    '''
    @param: G, a nx.DiGraph obj
    @return：{}  upath2, all unbalance unbpath, 
    '''
    upath2 = []
    def is_unp(s,t):
        if s is t or G.out_degree(s) <= 1:
            return None
        firstPath = None
        for path in all_simple_paths(G,s,t):
            #第一条路径
            if firstPath is None:
                firstPath = path
            #如果有一条路径和第一条路径不相等，那么就说明是UNP,返回一个元组
            elif len(path) != len(firstPath):
                return ((s, t), [path])
                #return ((s,t), list(nx.all_simple_paths(G,s,t)))
        #循环之后没有退出，说明每一条都和第一条相等，则返回None，说明不是UNP
        return None
    for s in G.nodes_iter():
        if cc.isPort(s) and s.port_type == cc.Port.PORT_TYPE_OUTPUT:
            continue
        for t in G.nodes_iter():
            if cc.isPort(s) and s.port_type == cc.Port.PORT_TYPE_OUTPUT:
                continue
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
    nodes = [node for node in G.nodes() if G.out_degree(node)>1]
    for s in nodes:
        upath[s] = find_upath(G, s)
    upath = {(s,t):[] for s in upath.keys() for t in upath[s]}
    return upath
    
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
