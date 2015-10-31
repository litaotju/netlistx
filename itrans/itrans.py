# -*-coding:utf-8 -*- #
u'''将iscas89电路门级网表提取出图，并且构建CloudRegGraph。
   将中间结果和最终的结果生成。dot格式的图保存在子目录中。
   只适合作为主调模块来使用。
'''
import re
import os
import sys
import copy
from exceptions import *

import networkx as nx
import matplotlib.pylab as plt

from netlistx.prototype.unbpath import unbalance_paths
from netlistx.file_util import vm_files
from Primitives import *

def trans(filename):
    '''@param: filename , iscas89的 Verilog网表文件
       @return： prims列表，列表的每一个元素是一个tuple = （cellref, name, ports）
       @brief: 输入文件识别每一个 prim instance，并返回全部列表
    '''
    #       cellref name(output,input1,input2, input3)
    ipattern = r'(\w+)\s+(\w+)\(((?:\w+,?)+)\);'
    begin = False
    fobj = open(filename, 'r')
    prims = []
    lino = 0
    for line in fobj:
        lino += 1
        stm = line.strip()
        if stm == '':
            continue
        if not begin:
            if stm.startswith("module s"):
                begin = True
            continue
        else:
            match = re.match(ipattern, stm)
            if stm.split()[0] in primtypes:
                if match is None:
                    print "Warning:%s %d, %s" % (filename, lino, line)
            if match is not None:
                words = match.groups()
                cellref = words[0]
                name    = words[1]
                ports   = words[2].split(",")
                prims.append ((cellref, name, ports ))
    fobj.close()
    return prims

def classify(prims):
    '''@param: prims,  a list of tuple (cellref, name, ports )
       @return: dffs, Dff对象的列表
                coms, Combi对象的列表
       @biref：对实例化原语进行分类，并且建立内部对象
    '''
    dffs = []
    coms = []
    for cellref, name, ports in prims:
        assert cellref in primtypes, "undefined %s %s" % (cellref, name)
        if cellref == dffkeyword :
            assert len(ports) == 3, name
            dffs.append( Dff(name, ports[0], ports[1], ports[2] ))
        else:
            coms.append( Combi(cellref, name, ports[0], ports[1:]) )
    return dffs, coms

def graphy(dffs, coms, name):
    '''@param: dffs, Dff对象的列表
                coms, Combi对象的列表
                name，想要生成的图的名称
       @return: g, A networkx DiGraph obj 
                g的节点是 input, output,和prim.每一个节点都是字符串
                g的边是他们之间的连接
    '''
    g = nx.DiGraph()
    g.name = name
    prims = dffs+coms
    for prim in prims:
        node = prim.name
        nodeshape = "box" if prim.cellref == dffkeyword else "ellipse"
        nodecolor = 'red' if prim.cellref == dffkeyword else "black"
        g.add_node(node, label = prim.cellref, shape = nodeshape, color = nodecolor )
    cnt_dict = {} # key = wirename 
    for prim in prims:
        name = prim.name
        inputs = [prim.input] if prim.cellref == dffkeyword else prim.inputs
        output = prim.output
        if not cnt_dict.has_key(output):
            cnt_dict[output] = {'source':name, 'target':[]}
        else:
            assert cnt_dict[output]['source'] is None, "%s has two source.They are: %s %s" % \
                           (output, cnt_dict[output]['source'], name)
            cnt_dict[output]['source'] = name
        for wire in inputs:
            if not cnt_dict.has_key(wire):
                cnt_dict[wire] = {'source':None , 'target':[]}
            cnt_dict[wire]['target'].append( name)
            
    pis = [ key for key in cnt_dict.keys() if cnt_dict[key]['source'] is None ]
    pos = [ key for key in cnt_dict.keys() if len(cnt_dict[key]['target'])==0 ]
    for wire, connect in cnt_dict.iteritems():
        source = connect['source']
        for target in connect['target']:
            if source is None:
                # PI
                g.add_node(wire, label = 'input')
                g.add_edge( wire, target)
            else:
                g.add_edge(source, target)
        # wire is PO 
        if len(connect['target']) == 0:
            g.add_node(wire, label = 'output')
            g.add_edge(source, wire)
    return g

def report_fanout(g):
    '''给一个图，打印图中label为dffkeyword的节点的扇出度，返回扇出个数的统计。
        前提是每一个D触发器都需要有label
    '''
    assert isinstance(g, nx.DiGraph )
    label = nx.get_node_attributes(g, 'label')
    fds = [fd for fd in label.keys() if label[fd] == dffkeyword ]
    fanouts = {}
    for fd in fds:
        fanout = g.out_degree(fd) 
        if not fanouts.has_key(fanout):
            fanouts[ fanout ] = 1
        else:
            fanouts[ fanout] += 1
    print "fanout fd-number:"
    print "\n".join( [ str((key, val)) for key, val in fanouts.iteritems() ] )
    return fanouts

def crgraph(g):
    #传进来的图每一个节点都是字符串。label属性是他们的cellref
    assert isinstance(g, nx.DiGraph)
    gg = g.copy()
    label = nx.get_node_attributes(gg, 'label')
    fds = [node for node in gg.nodes() if label[node] == dffkeyword]
    gg.remove_nodes_from( fds )
   
    cr = nx.DiGraph()
    cr.name = gg.name+"_crgraph"
    clouds = []
    ccnt = 0
    for cloud in nx.weakly_connected_component_subgraphs(gg):
        assert isinstance(cloud, nx.DiGraph )
        ccnt += 1
        cloud.name = "cloud%d" % ccnt 
        clouds.append( cloud )
        cr.add_node(cloud, label = cloud.name)
    cr.add_nodes_from(fds, label = dffkeyword)

    empty_cnt = 0
    for edge in g.edges_iter():
        pre = edge[0]
        succ = edge[1]
        credge = ()
        if  label[pre] == dffkeyword and label[succ] == dffkeyword:
            empty = nx.DiGraph(name = 'empty%d'% empty_cnt )
            empty_cnt += 1
            cr.add_edge( pre, empty )
            cr.add_edge( empty, succ )
            continue
        elif label[pre] != dffkeyword and label[succ] == dffkeyword:
            for cloud in clouds:
                if cloud.has_node(pre):
                    credge = (cloud, succ)
            if not credge:
                print "None of the cloud has prim: %s %s.in edge:%s" % (label[pre], pre, str(edge) )
                print "that node in originnal graph:",
                print "precs:%s succs:%s" %( str(g.predecessors(pre)), str(g.successors(pre)) )
                raise AssertionError
        elif label[pre] == dffkeyword and label[succ] != dffkeyword:
            for cloud in clouds:
                if cloud.has_node( succ):
                    credge = (pre, cloud)
            if not credge:
                print "None of the cloud has prim: %s %s.in edge:%s" % (label[succ], succ, str(edge))
                print "that node in originnal graph:"
                print "precs:%s succs:%s" %( str(g.predecessors(succ)), str(g.successors(succ)) )
                raise AssertionError
        else:
            continue
        cr.add_edge(credge[0], credge[1] )
    cr.fds = fds
    cr.clouds = clouds
    return clouds, fds, cr 

def merge(fds, cr):
    #将每一个FD的扇出合并到一个Cloud
    assert isinstance( cr, nx.DiGraph)
    for fd in fds:
        succs = cr.successors( fd)
        if len(succs ) <= 1:
            continue
        else:
            big_cloud = nx.union_all(succs)
            big_cloud.collection = [succ.name for succ in succs]
        pre_fds = set()
        succ_fds = set()
        for succ_cloud in succs:
            assert isinstance(succ_cloud, nx.DiGraph)
            pre_fds = pre_fds.union( set( cr.predecessors(succ_cloud) ) )
            succ_fds = succ_fds.union( set( cr.successors( succ_cloud) ) )
            cr.remove_node(succ_cloud)
        cr.add_node( big_cloud, label ='bigcloud')
        cr.add_edges_from( [ (pre_fd, big_cloud) for pre_fd in pre_fds] )
        cr.add_edges_from( [ (big_cloud, succ_fd) for succ_fd in succ_fds] )
    for fd in fds:
        if cr.out_degree(fd) != 1 or cr.in_degree(fd) != 1:
            print "Error: %s indegree:%d outdegree:%d" % (fd, cr.in_degree(fd), cr.out_degree(fd) )
            raise AssertionError
    return cr

def fd2edge(fds, cr):
    assert isinstance(cr, nx.DiGraph)
    arc = {}
    for fd in fds:
        precs = cr.predecessors( fd )
        succs = cr.successors( fd )
        assert len(precs) == 1 and len(succs) == 1
        prec = precs[0]
        succ = succs[0] 
        assert isinstance(prec, nx.DiGraph)
        assert isinstance(succ, nx.DiGraph)
        if not arc.has_key( (prec, succ) ):
            arc[ (prec, succ )] = []
        arc[(prec, succ)].append( fd )
        cr.remove_node( fd )
    assert cr.number_of_edges() == 0
    remain_reg = 0
    for edge, reg in arc.iteritems():
        fdnum = len(reg )
        remain_reg += fdnum
        cr.add_edge(edge[0], edge[1], weight = fdnum, label = fdnum)
    if remain_reg != len(fds):
        print "Error: %d/%d fd remains in crgraph" % (remain_reg, len(fds))
        raise AssertionError
    return cr, arc

#---------------------------------------------------------------------------------

def main(path):
    '''输入一个路径，提取该路径下的iscas所有v或者vm文件，并且建立子文件夹，存储
    生成的graph,crgraph,mergegraph,finalgraph的图的dot文件。
    '''
    for vmfile in vm_files( path ):
        
        #输入输出环境搭建
        name = os.path.splitext(vmfile)
        inputfile = os.path.join(path, vmfile)
        outpath = os.path.join(path, name[0])
        if not os.path.exists(outpath):
            os.mkdir( outpath)
        print "Start ", inputfile

        #翻译，分拣
        prims = trans(inputfile )
        dffs, coms = classify(prims)
        
        #建图
        g = graphy(dffs, coms, name[0])
        print "Graph Fanout:"
        fanouts = report_fanout(g)
        gfilename = os.path.join( outpath,  g.name+".dot")
        nx.write_dot(g, gfilename)
        
        #构建cr
        clouds, fds, cr = crgraph(g)
        print "Crgraph Fanout before merging:"
        fanout = report_fanout(cr )
        crfilename = os.path.join( outpath, cr.name+".dot" )
        nx.write_dot(cr, crfilename)
        for cloud in clouds:
           cloudfilename = os.path.join( outpath, cloud.name+".dot")
           nx.write_dot( cloud, cloudfilename) 

        #合并每一个D触发器的扇出Cloud
        mergefile = os.path.join( outpath, cr.name+"_merge.dot")
        cr = merge(fds, cr)
        nx.write_dot( cr, mergefile) 
        
        #将D触发器全部化成边，边的权重就是寄存器的数量
        cr, arc = fd2edge(fds, cr)
        fd2edgefile = os.path.join(outpath, cr.name+"_final.dot")
        nx.write_dot(cr, fd2edgefile)

        #将最终的Cloud的情况全部写入一个文件夹的dot中
        finalpath= os.path.join(outpath, 'final')
        if not os.path.exists( finalpath ):
            os.mkdir( finalpath)
        cloudname = []
        for cloud in cr.nodes():
            assert cloud.name not in cloudname,\
                "Cr:%s Different cloud has same name. %s" % (cr.name, cloud.name)
            cloudname.append( cloud.name )
            finalcloud = os.path.join( finalpath, cloud.name+".dot")
            nx.write_dot(cloud, finalcloud) 
        print "Hadling ", vmfile, "OK"

#---------------------------------------------------------------------------------
#和最优化问题有关系的函数

def getgraph(filename):
    '''@param: filename， 一个可以打开的文件名，可以是绝对路径也可以是相对路径
       @return: cr, 根据该文件生成的cr图，
    '''
    prims = trans(filename )
    name = os.path.split(filename)[1]
    basename = os.path.splitext(name)
    dffs, coms = classify(prims)
    g = graphy(dffs, coms, basename[0])
    clouds, fds, cr = crgraph(g)
    cr = merge(fds, cr)
    cr, eweight = fd2edge(fds, cr)
    return cr, eweight

def upath_cycle(cr):
    '''@ param: cr, a nx.DiGraph,每一个节点必须有一个独特的name属性与其他节点不同
       @ return: upaths, cycles ,图中所有的不平衡路径和环
       @ brief: 将每一个图转化成节点的名字为节点的图，然后找出图中所有的不平衡路径和环
    '''
    namegraph = nx.DiGraph()
    for edge in cr.edges():
        namegraph.add_edge( edge[0].name, edge[1].name )
        
    upaths = unbalance_paths( namegraph)
    #realpath = []
    #for upath in upaths.values():
    #    if len(upath) != 0:
    #        realpath += upath
    cycles = []
    for cycle in nx.simple_cycles(namegraph):
        cycles.append( cycle)
    return upaths, cycles

def search_unbalance_iscas(path):
    '''@param:path, 存放网表文件的有效路径
       @return： None
       @brief: 对该目录下的每一个网表进行图的建模，生成不平衡路径写入文件中。
    '''
    records = open(path+"\\upath.log",'w')
    for vmfile in vm_files( path ):
        filename = os.path.join( path, vmfile )
        print "Handling ", vmfile
        cr, ewight = getgraph( filename )
        upaths, cycles = upath_cycle(cr )
        
        # 重定向标准输出
        console = sys.stdout
        sys.stdout = records
        
        #将环和不平衡路径写入文件
        sys.stdout = console
        records.write("\n\n"+cr.name+"\nupath:")
        for upath in upaths:
            records.write(str(upath)+"\n" )
        records.write('cycles:\n')
        for cycle in cycles:
            records.write( str(cycle)+"\n")
        
        #最优化问题建立
        convert2opt(cr, ewight, upaths, cycles)
    
    records.close()
    print "All unbalances found"
    return None

def convert2opt(cr, ewight, upaths, cycles):
    '''转化成Matlab求解的方法
    '''
    names ={ node:node.name for node in cr.nodes() }
    namewight = {}
    for edge, weight in ewight.iteritems():
        name0 = names[ edge[0] ]
        name1 = names[ edge[1] ]
        assert not namewight.has_key( (name0, name1) )
        namewight[(name0, name1)] = len(weight)

    edge2x = {}       #名称字典,键为边，值为X变量的索引
    all_edges = {}    #权重字典,键为边，值为权重
    cycle_const = []
    
    # 下面字典的每一个Key是（s,t）tuple，值是s.t之间的所有路径的列表
    unbalance_const = {}
    for (s,t), path_bwt in upaths.iteritems():
        unbalance_const[ (s,t) ] = []
        for upath in path_bwt:
            edges = []

            if upath[0] == upath[-1]:
                #环的情况跳过去
                continue
            else:
                for i in range(0, len(upath)-1):
                    edge = (upath[i], upath[i+1])
                    edges.append( edge )
                    all_edges[ edge ] = namewight[ edge ]
                unbalance_const[ (s,t) ].append( edges )
    
    # 下面进行cycles列表的获取
    for cycle in cycles:
        edges = []
        for i in range(0, len(cycle)-1 ):
            edge = (cycle[i], cycle[i+1]) 
            edges.append( edge )
            all_edges[ edge ] = namewight[ edge ]
        back_edge = (cycle[-1], cycle[0])
        all_edges[ back_edge ] = namewight[ back_edge ]
        edges.append( back_edge )
        cycle_const.append( edges )
    
    # 准备进行权重和约束的输出
    cnt = 0
    sorted_wight = []
    for edge, wight in all_edges.iteritems():
        cnt += 1 
        edge2x[ edge ] = "x(%d)" %cnt
        #print "%% %s : x%d" % (str( (names[ edge[0]], names[ edge[1] ])), cnt )
        sorted_wight.append( wight)
    
    #权重的字符串形式
    print "%% Weight of Edges"
    print "W = ", str(sorted_wight )

    cycle_string_const = [] #环约束的字符串形式
    for cycle in cycle_const:
        xs = []
        for edge in cycle:
            xs.append( edge2x[edge])
        string = "*".join( xs )
        string = string+ "<= 1/100000 ;"
        cycle_string_const.append( string )
    print "%% Cycle Constraits Are:"
    print "\n".join( cycle_string_const)
    
    print "%% Unbalance Constraints Are:"
    unbalance_string_const = [] #不平衡路径的每一项的乘积的字符串
    for (s,t), paths_between in unbalance_const.iteritems():
        length_dict = {}
        #把路径按照长度来归类。
        for upath in paths_between:
            n = len( upath ) 
            if not length_dict.has_key( n ):
                length_dict[n] = ""
            else:
                xs = []
                for edge in upath:
                    xs.append( edge2x[ edge])
                string = "*".join( xs)
                length_dict[n] = length_dict[n]+"*"+string

        length_list = length_dict.values()
        n = len( length_list )
        for i in range(0, n-1):
            for j in range(0, n-1):
                if i==j:
                    continue
                else:
                    print length_list[i]+"*"+length_list[j] + "<= 1/100000;"
                    
    all_un_constraints = []
    

    print "Unbalance SOM is:"
    print "\n".join( unbalance_string_const)

    return None

#------------------------------------------------------------------------------------
if __name__ == "__main__":
    print u"请输入符合iscas格式的电路网表所在文件夹："
    path = raw_input("plz enter file path:>")
    assert os.path.exists( path)
    while(True):
        job = raw_input("plz enter the job: grh? balance?>:")
        if job == "grh":
            main(path)
            break
        elif job == "balance":
            search_unbalance_iscas(path)
            break
        elif job == "exit":
            break
        else:
            continue
