# -*- coding:utf-8 -*- #
# from Queue import Queue
'''对于完全图来说，整个算法所需要的消耗的时间好像太长了，以及算法所发现的不平衡边，太多了。
N = 4的完全图中，有36条不平衡路径。
'''
import networkx as nx

def unbalance_paths(G):
	'''
	@param: G, a nx.DiGraph obj
	@return：{}  upath2, all unbalance unbpath, 
			 key: multi fanout node A, value: paths from A
	'''
	upath = {}
	upath2 = {}
	nodes = [node for node in G.nodes() if G.out_degree(node)>1]
	for s in nodes:
		upath[s] = find_upath(G, s)
		upath2[s] = [] 
		for t in upath[s]:
			upath2[s] += nx.all_simple_paths(G, s, t)
	return upath2
	
def find_upath(G, s):
	'''@param: G, an DiGraph obj
			 : s, a node in G
	   @return: reconvergent nodes in from s.
	'''
	# print "Searching node: %s" % s
	time = 0
	depth = {}
	depth[s] = [0]
	reconvergent_nodes = []
	
	bfs_list = G.succ[s].keys()
	while(len(bfs_list) != 0 ):
		time += 1
		next_list = []
		for node in bfs_list:
			if node is s:
				# print "A loop contained s found"
				continue
			if node not in depth.keys():
				depth[node] = []
			else:
				# print "Node:%s depth:%d" % ( str(node), time )
				if node not in reconvergent_nodes:
					reconvergent_nodes.append(node)
			depth[node].append(time)
			for next_level_node in G.succ[node].keys():
				if next_level_node  in next_list or next_level_node in depth.keys():
					if next_level_node in depth.keys():
						# print "A reverse Edge: %s %s " % (node , next_level_node)
						continue	
				next_list.append(next_level_node)
		bfs_list = next_list 
	return reconvergent_nodes
#----------------------------------------------------------------------------------

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
	
if __name__ == "__main__":
	G = nx.DiGraph()
	edges = [
		('a', 'b'),('a', 'c'),('a','d'),('c','d'),
		('b','c'),('b','d')
		# ('c', 'e'),('d','e'),
		# ('e','f'),('a','a'),
	]
	G.add_edges_from(edges)
	# r = find_upath(G, 'a')
	# print r

	# print "Un-balance Paths:"
	# for key , val in u.items():
	# 	print "%s %s " % (str(key), str(val))

