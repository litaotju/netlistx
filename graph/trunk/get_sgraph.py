
def get_s_graph(self):
    '''
        >>>self.s_graph.copy(),根据已有的图来生成s-graph
        生成的s图完全是nx.DiGraph类的，不是自定义类，初步评估发现，用这种方法
        生成s图比 原先graph_s_graph中的只处理边集和点集更快速。所以有必要修改
        该类的定义和构造函数。
    '''
    care_type=('FD')
    ##step1
    ##无聊的初始化过程，先建一个s_graph的对象，然后直接对数据属性进行赋值
    s1=s_graph(self.include_pipo)
    s1.name=self.name
    if self.include_pipo:
        for x in self.pipo_vertex_list:
            if x.port_type=='input':
                s1.pi_nodes.append(x)
            else:
                s1.po_nodes.append(x)
    for fd in self.prim_vertex_list:
        if fd.m_type=='FD':
            s1.fd_nodes.append(fd)
    ##为DiGraph内核添加节点与边
    s1.add_nodes_from(self.vertex_set)
    for eachEdge in self.edge_set:
        s1.add_edge(eachEdge[0][0],eachEdge[0][1],\
                port_pair=eachEdge[1],cnt=eachEdge[2])
    node_type_dict=nx.get_node_attributes(self,'node_type')   
    
    ##step2
    ##ignore 每一个非FD的primitive节点
    new_edge=[]
    for eachNode in self.nodes_iter():
        if node_type_dict[eachNode] not in ['input','output']:
            if eachNode.m_type not in care_type:
                pre=[]
                suc=[]
                pre=s1.predecessors(eachNode)
                suc=s1.successors(eachNode)
                s1.remove_node(eachNode)
                if pre and suc:
                    for eachS in pre:
                        for eachD in suc:
                            new_edge.append((eachS,eachD))
                            s1.add_edge(eachS,eachD)
    ##为新添加的边归类，
    s1.new_edges=new_edge
    self.s_graph=s1
    return s1.copy()