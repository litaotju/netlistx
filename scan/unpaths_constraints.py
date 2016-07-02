#-*- coding: utf-8 -*-
u'''各种不同的产生UNP约束的方法
'''
def upaths_contraints_complex(unpaths, node2x):
    u'''UNP相交的情况，考虑全部约束，否则只考虑起点和终点
    '''
    unpath_constraints = []
    upaths_set = {}
    for (source, target), paths_between in unpaths.iteritems():
        temp_set = reduce(lambda x, y: x.union(set(y)), paths_between, set())
        upaths_set[(source, target)] = temp_set

    upaths_has_common = {}
    for (source, target), temp_set in upaths_set.iteritems():
        has_common = False
        for (source1, target1), temp_set1 in upaths_set.iteritems():
            if (source1, target1) == (source, target):
                continue
            elif not temp_set.isdisjoint(temp_set1):
                has_common = True
                break
        upaths_has_common[(source, target)] = has_common

    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # 如果和其他的都不相交
        if not upaths_has_common[(source, target)]:
            e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
            unpath_constraints.append(e)
        else:
            # length: [paths]
            length_dict = {}
            # 把路径按照长度来归类.同一个长度的不平衡路径全部乘起来，称之为Ki
            for upath in paths_between:
                length = len(upath)
                string = tuple([node2x[node] for node in upath])
                if length not in length_dict:
                    length_dict[length] = [string]
                else:
                    length_dict[length].append(string)
            #[paths][paths][paths]
            length_list = length_dict.values()
            products = []
            # print "%% (%s, %s)" % (source, target)
            for i in range(0, len(length_list) - 1):
                for j in range(i + 1, len(length_list)):
                    for path_in_group_i in length_list[i]:
                        for path_in_group_j in length_list[j]:
                            products.append(
                                set(path_in_group_i).union(set(path_in_group_j)))
            for product in products:
                unpath_constraints.append("+".join(product) +
                                          "<= %d;..." % (len(product) - 1))
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

def upaths_contraints_stupid(unpaths, node2x):
    u'''原始的最2B的求约束的方法，长度分组，然后相加
    '''
    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # length: [paths]
        length_dict = {}
        # 把路径按照长度来归类.同一个长度的不平衡路径全部乘起来，称之为Ki
        for upath in paths_between:
            length = len(upath)
            string = tuple([node2x[node] for node in upath])
            if length not in length_dict:
                length_dict[length] = [string]
            else:
                length_dict[length].append(string)
        #[paths][paths][paths]
        length_list = length_dict.values()
        products = []
        # print "%% (%s, %s)" % (source, target)
        for i in range(0, len(length_list) - 1):
            for j in range(i + 1, len(length_list)):
                for path_in_group_i in length_list[i]:
                    for path_in_group_j in length_list[j]:
                        products.append(
                            set(path_in_group_i).union(set(path_in_group_j)))
        for product in products:
            unpath_constraints.append("+".join(product) +
                                        "<= %d;..." % (len(product) - 1))
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

##---------------------------------------------------------------
def upaths_contraints_more_complex(unpaths, node2x):
    u'''brief:
            对每一个UNP，判断其中每一个长度分组内的不平衡路径的是否和其他UNP有交集
                如果有，在约束中，将这一组的全部写出来
                如果没有，在约束中，将一组只认为是一条边
            同时，更新node2x的对应关系
        @params:
            unpaths, a dict of {(source:target):[[path1][path2]...]}
            node2x, a dict of { node:x(%d)}
        @return:
            upaths_contraints, a list of equation in string form, ["x1+x2<=1;...", "x2+x3<=1;..."...]
        @modify:
            modify the node2x
    '''
    upaths_set = {}
    
    #对每一个UNP的不平衡路径按照长度分组
    upaths_length_group_set = {}
    for (source, target), paths_between in unpaths.iteritems():
        temp_set = reduce(lambda x, y: x.union(set(y)), paths_between, set())
        upaths_set[(source, target)] = temp_set
        # length: [paths]
        length_dict = {}
        for upath in paths_between:
            length = len(upath)
            string = tuple([node2x[node] for node in upath])
            if length not in length_dict:
                length_dict[length] = [string]
            else:
                length_dict[length].append(string)
        #[paths][paths][paths]
        length_list = length_dict.values()
        upaths_length_group_set[(source, target)] = length_list

    upaths_has_common = {}
    group_has_common = {}
    
    ##求每一组是否和其他UNP中的一组有交集
    get_set_from_list_list = lambda group: reduce(lambda x, y: x.union(set(y[1:-1])), group, set())
    for (source, target), groups in upaths_length_group_set.iteritems():
        has_common = False
        for (source1, target1), groups1 in upaths_length_group_set.iteritems():
            if (source1, target1) == (source, target):
                continue
            for group in groups:
                #如果这一组已经判断过且和其他UNP中的某一组有交点，则直接跳过。判定此UNP和其他有交点
                if group_has_common.has_key((source,target,len(group[0]))):
                    has_common = True
                    continue
                # 一组内的所有路径上的所有内点，全部化为一个集合
                tempset = get_set_from_list_list(group)
                for group1 in groups1:
                    tempset1 = get_set_from_list_list(group1)
                    if tempset.intersection(tempset1):
                        has_common = True
                        group_has_common[(source,target,len(group[0]))] = True
                        group_has_common[(source1,target1,len(group1[0]))] = True
        upaths_has_common[(source, target)] = has_common
        upaths_has_common[(source1, target1)] = has_common

    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # 如果和其他的都不相交
        if not upaths_has_common[(source, target)]:
            e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
            unpath_constraints.append(e)
        else:
            #[paths][paths][paths]
            length_list = upaths_length_group_set[(source, target)]
            new_length_list = []
            products = []
            for group in length_list:
                #如果这一组没有和其他的有交集
                if not group_has_common.has_key((source,target,len(group[0]))):
                    #只取一条路径
                    new_length_list.append(merge_group(group,node2x))
                else: #如果和其他的组有交集，则取这一组全部的路径
                    new_length_list.append(group)
            length_list = new_length_list
            for i in range(0, len(length_list) - 1):
                for j in range(i + 1, len(length_list)):
                    for path_in_group_i in length_list[i]:
                        for path_in_group_j in length_list[j]:
                            products.append(
                                set(path_in_group_i).union(set(path_in_group_j)))
            for product in products:
                unpath_constraints.append("+".join(product) +
                                          "<= %d;..." % (len(product) - 1))
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints

def merge_group(group, node2x):
    u'''@breif:
            把一组同样长度（group内的路径）的不平衡路径替换成，一条路径，上面的每一个点的权重为组内路径的个数
        @params:
            group, a list of list, each of the list has same length
            node2x, dict {node->x }
        @return:
            [group[0]]
        @modifiy:
            node2x
    '''
    # len group >= 2
    # group中的每一个列表长度相等
    #对第一条之外的其他路径操作
    for i in range(1, len(group)):
        #内点, 将多个节点，映射为一个x
        for index, node in enumerate(group[i]):
            assert index < len(group[0])
            if index == 0 or index == len(group[i])-1:
                continue
            node2x[node] = node2x[group[0][index]]
    return [group[0]]

##---------------------------------------------------------------
def partial_merge_group(unp, path_has_common, group, node2x):
    no_common_paths = []
    common_paths = []
    for path in group:
        if path_has_common.has_key((unp[0],unp[1],len(group[0]),tuple(path))):
            common_paths.append(path)
        else:
            no_common_paths.append(path)
    if no_common_paths:# 如果有和其他UNP没有任何交集的路径，则将这些路径和为一组
        no_common_paths = merge_group(no_common_paths, node2x)
    new_group = no_common_paths + common_paths
    return new_group

def has_common(upaths_length_group_set):
    u'''查看每一条路径是否和别的有交集
    '''
    upaths_has_common = {}
    group_has_common = {}
    path_has_common = {}
    ##求每一组是否和其他UNP中的一组有交集
    get_set_from_list_list = lambda group: reduce(lambda x, y: x.union(set(y[1:-1])), group, set())
    for (source, target), groups in upaths_length_group_set.iteritems():
        has_common = False
        for (source1, target1), groups1 in upaths_length_group_set.iteritems():
            if (source1, target1) == (source, target):
                continue
            for group in groups:
                for path in group:
                    if path_has_common.has_key((source,target,len(group[0]),path)):
                        has_common = True
                        continue
                    # 一组内的所有路径上的所有内点，全部化为一个集合
                    tempset = set(path)
                    for group1 in groups1:
                        for path1 in group1:
                            tempset1 = set(path1)
                            if tempset.intersection(tempset1):
                                has_common = True
                                group_has_common[(source,target,len(group[0]))] = True
                                group_has_common[(source1,target1,len(group1[0]))] = True
                                path_has_common[(source,target,len(group[0]),path)] = True
                                path_has_common[(source1,target1,len(group1[0]),path1)] = True
        upaths_has_common[(source, target)] = has_common
        upaths_has_common[(source1, target1)] = has_common
    return upaths_has_common, group_has_common, path_has_common

def upaths_contraints_moremore_complex(unpaths, node2x):
    u'''brief:
            对每一个UNP，判断其中每一个长度分组内的不平衡路径的是否和其他UNP有交集
                如果有，在约束中，将这一组的全部写出来
                如果没有，在约束中，将一组只认为是一条边
            同时，更新node2x的对应关系
        @params:
            unpaths, a dict of {(source:target):[[path1][path2]...]}
            node2x, a dict of { node:x(%d)}
        @return:
            upaths_contraints, a list of equation in string form, ["x1+x2<=1;...", "x2+x3<=1;..."...]
        @modify:
            modify the node2x
    '''
    upaths_set = {}
    
    #对每一个UNP的不平衡路径按照长度分组
    upaths_length_group_set = {}
    for (source, target), paths_between in unpaths.iteritems():
        temp_set = reduce(lambda x, y: x.union(set(y)), paths_between, set())
        upaths_set[(source, target)] = temp_set
        # length: [paths]
        length_dict = {}
        for upath in paths_between:
            length = len(upath)
            string = tuple([node2x[node] for node in upath])
            if length not in length_dict:
                length_dict[length] = [string]
            else:
                length_dict[length].append(string)
        #[paths][paths][paths]
        length_list = length_dict.values()
        upaths_length_group_set[(source, target)] = length_list

    upaths_has_common = {}
    group_has_common = {}
    path_has_common = {}
    upaths_has_common, group_has_common, path_has_common = has_common(upaths_length_group_set)
    # 获取不平衡路径约束
    unpath_constraints = []
    for (source, target), paths_between in unpaths.iteritems():
        # 如果和其他的都不相交
        if not upaths_has_common[(source, target)]:
            e = "%s+%s<= 1;..." % (node2x[source], node2x[target])
            unpath_constraints.append(e)
        else:
            #[paths][paths][paths]
            length_list = upaths_length_group_set[(source, target)]
            new_length_list = []
            products = []
            for group in length_list:
                #如果这一组没有和其他的有交集
                if not group_has_common.has_key((source,target,len(group[0]))):
                    #只取一条路径
                    new_length_list.append(merge_group(group,node2x))
                else: #如果和其他的组有交集，将有交集的单独拿出来
                    new_length_list.append(
                        partial_merge_group((source,target), path_has_common,
                                            group,
                                            node2x)
                        )
            length_list = new_length_list
            for i in range(0, len(length_list) - 1):
                for j in range(i + 1, len(length_list)):
                    for path_in_group_i in length_list[i]:
                        for path_in_group_j in length_list[j]:
                            products.append(
                                set(path_in_group_i).union(set(path_in_group_j)))
            for product in products:
                unpath_constraints.append("+".join(product) +
                                          "<= %d;..." % (len(product) - 1))
    logger.critical("ESGraph generated %d matlab upath constraints" %
                    len(unpath_constraints))
    return unpath_constraints