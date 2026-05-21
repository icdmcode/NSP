import csv
import ast
import sys
import time
import psutil
import math
# 增加字段大小限制
csv.field_size_limit(2**31 - 1)
startTimestamp = 0
endTimestamp = 0
maxMemory = 0
# sys.stdout = open('output1.txt', 'w', encoding='utf-8')

def read(filename):
    # 读取输入文件
    S = []
    with open(filename, 'r') as input:
        for line in input:
            # 移除行末的 '-2'
            line = line.strip().rstrip('-2')
            elements = line.split('-1')  # 根据 '-1' 分割元素
            # print(elements)
            s = []
            for e in elements:
                # 将非空字符串分割成列表，确保元素内部的空格被正确处理
                if e.strip():
                    s.append(e.split())
            # print(s)
            S.append(s)
    print("输入数据库")
    # print(S)
    return S


def parse_pattern(pattern_str):
    # 去除最外层的中括号
    pattern_str = pattern_str[1:-1]
    # 分割项集
    itemsets = pattern_str.split("], [")
    pattern = []
    for itemset_str in itemsets:
        if itemset_str:  # 非空项集
            itemset = itemset_str.split(", ")
            itemset = [item.strip("[]") for item in itemset]
            pattern.append(itemset)
        else:
            pattern.append([])
    return pattern


def read_patterns_from_csv(file_path):
    patterns = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过标题行
        for row in reader:
            pattern = parse_pattern(row[0])
            support = int(row[1])
            size = int(row[2])
            sid_list = ast.literal_eval(row[3])
            patterns.append(SequentialPattern(pattern, support, sid_list))
    return patterns


class SequentialPattern:
    def __init__(self, pattern, support, sid_list=None):
        self.pattern = pattern
        self.support = support
        self.size = len(pattern)  # 元素（项集）的数量（不是项的数量）
        self.sid_list = sid_list if sid_list else []

    def __repr__(self):
        sid_str = ', '.join(map(str, self.sid_list))
        # 在字符串表示中包含size属性
        return f"SequentialPattern({self.pattern}, {self.support}, size={self.size}, sids=[{sid_str}])"
# 以上不需要修改


# 定义一个函数来去掉否定符号 ¬ 并返回修改后的模式
def remove_negation_symbols(pattern):
    # 遍历每个项集
    for i, itemset in enumerate(pattern):
        # 遍历项集中的每个项
        for j, item in enumerate(itemset):
            # 如果项以 ¬ 开头，去掉 ¬ 符号
            if item.startswith('¬'):
                pattern[i][j] = item[1:]
    return pattern


# 计算模式的支持度
def calculate_support(pattern, dataset_size, psp_list):
    # psp_support_dict = {tuple(tuple(item) for item in psp.pattern): psp.support for psp in psp_list}
    # psp_supsid_dict = {tuple(tuple(item) for item in psp.pattern): psp.sid_list for psp in psp_list} # 补充
    nsc = [itemset[:] for itemset in pattern] # 注意创建一个浅拷贝，一开始这里耽误了好久！
    # print("调试NSC")
    # print(nsc)

    # 提取 NSC 中的否定项，只有当存在否定项时才添加
    negated_items = []
    for itemset in nsc:
        negated_items_in_itemset = [item for item in itemset if item.startswith('¬')]
        if negated_items_in_itemset:  # 只有当存在否定项时才添加
            negated_items.append(negated_items_in_itemset)
    # print("调试negated_items")
    # print(negated_items)

    # positive_partner（即去掉nsc中所有的¬符号）
    nsc1 = [itemset[:] for itemset in nsc]
    positive_partner = remove_negation_symbols(nsc1)
    # print("调试positive_partner")
    # print(positive_partner)
    # print(nsc)
    # MPS
    MPS = []
    for itemset in nsc:
        non_negated_items_in_itemset = [item for item in itemset if not item.startswith('¬')]
        if non_negated_items_in_itemset:  # 只有当存在非否定项时才添加
            MPS.append(non_negated_items_in_itemset)
    # print("调试MPS")
    # print(MPS)

    # 如果NSC只有一个元素（项集）
    # if len(nsc) == 1:
    if len(nsc) == 1 and len(negated_items) == 1:
        # 计算支持度
        p_nsc_support = psp_support_dict.get(tuple(tuple(item) for item in positive_partner), 0)
        nsc_support = dataset_size - p_nsc_support

    # 如果NSC元素（项集）数大于1
    # else:
    elif len(nsc) > 1 and len(negated_items) == 1:
        # 计算支持度
        mps_nsc_support = psp_support_dict.get(tuple(tuple(item) for item in MPS), 0)
        p_nsc_support = psp_support_dict.get(tuple(tuple(item) for item in positive_partner), 0)
        nsc_support = mps_nsc_support - p_nsc_support

    # Algorithm 2当中最后一个else分支
    else:
        # 计算支持度
        mps_nsc_support = psp_support_dict.get(tuple(tuple(item) for item in MPS), 0)

        # 空集合
        union = set()

        p_negated_items = remove_negation_symbols(negated_items)

        for p_neg_item in p_negated_items:
            p_neg_item_sid = psp_supsid_dict.get(tuple(tuple(item) for item in p_neg_item), [])
            for sid in p_neg_item_sid:
                union.add(sid)

        nsc_support = mps_nsc_support - len(union)

    checkMemory()
    return nsc_support


# 最新完善：判断是否包含连续两个负元素（不合法的情况）
def contains_consecutive_negations(pattern):
    # 遍历模式中的每个项集，检查是否有连续的负元素
    for i in range(len(pattern) - 1):
        # 检查当前项集和下一个项集是否都包含负元素
        if pattern[i][0].startswith('¬') and pattern[i + 1][0].startswith('¬'):
            return True  # 找到连续负元素，返回True
    return False  # 没有找到连续负元素，返回False


from itertools import combinations
# 生成NSC（完整版：考虑包含>=2个负元素的情况）
def e_NSP_Candidate_Generation(psp, min_sup, len_dataset, psp_list):
    nsc_list = []
    # 遍历PSP的每个itemset
    # 枚举所有项集被否定的情况
    pattern_length = len(psp.pattern)
    for r in range(1, pattern_length + 1):
        for indices in combinations(range(pattern_length), r):
            # 创建新的NSP模式
            new_pattern = list(psp.pattern)  # 复制原始模式
            # 遍历被选中的索引，对相应的项集进行否定
            for i in indices:
                new_pattern[i] = ['¬' + item for item in new_pattern[i]]
            # print("new_pattern:", new_pattern)
            # print(contains_consecutive_negations(new_pattern))
            if contains_consecutive_negations(new_pattern):
                continue
            # print("new_pattern:", new_pattern)
            # 计算新模式的支持度
            support = calculate_support(new_pattern, len_dataset, psp_list)
            # 如果支持度满足最小支持度，则添加到NSP列表
            if support >= min_sup and not contains_consecutive_negations(new_pattern):
                nsc_list.append(SequentialPattern(new_pattern, support, []))
    checkMemory()
    return nsc_list


# 打印结果
def print_patterns(title, pattern_list):
    print(f"{title} Support Size sids")
    for pattern in pattern_list:
        # 使用join和' '创建分隔符，使输出更加整齐
        sid_str = ' '.join(map(str, pattern.sid_list))
        print(f"{pattern.pattern} {pattern.support} size={pattern.size} sids=[{sid_str}]")


def checkMemory():
    global maxMemory  # 声明 maxMemory 为全局变量
    # current_memory = (psutil.virtual_memory().total - psutil.virtual_memory().available) / 1024 / 1024

    # 获取当前进程的内存使用情况
    process = psutil.Process()
    mem_info = process.memory_info()
    # 获取当前进程使用的内存量（以字节为单位）
    mem_usage = mem_info.rss
    # 将内存使用量转换为MB
    current_memory = mem_info.rss / 1024 / 1024

    if current_memory > maxMemory:
        maxMemory = current_memory


if __name__ == "__main__":
    # 从文件中读取序列数据
    file_path = 'datasets/test.txt'
    dataset = read(file_path)

    # 采用精确算法（例如PrefixSpan）挖掘PSP的结果
    file_path = 'test/psp_list_test_0.4.csv'
    psp_list = read_patterns_from_csv(file_path) # 通过csv文件读入


    # psp_support_dict = {tuple(psp.pattern): psp.support for psp in psp_list}
    # 将每个SequentialPattern实例的pattern属性转换为元组的元组
    # psp_support_dict = {tuple(tuple(item) for item in psp.pattern): psp.support for psp in psp_list}
    # 模块级变量
    psp_support_dict = {tuple(tuple(item) for item in psp.pattern): psp.support for psp in psp_list}
    psp_supsid_dict = {tuple(tuple(item) for item in psp.pattern): psp.sid_list for psp in psp_list}  # 补充


    # 挖掘NSP
    # min_sup = 2  # 设置最小支持度
    min_sup = math.ceil(len(dataset)*0.4)
    nsp_list = []  # 存储最终的NSP列表

    maxMemory = 0
    startTimestamp = time.time()
    # print(startTimestamp)
    local_time = time.localtime(startTimestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(formatted_time)

    for psp in psp_list:
        NSP = e_NSP_Candidate_Generation(psp, min_sup, len(dataset), psp_list)
        if(len(NSP)):
            print(f"NSPs generated from PSP: {psp.pattern}")
        for nsp in NSP:
            print(f"NSP: {nsp}, Support: {nsp.support}")
        nsp_list.extend(NSP)  # 将生成的NSC列表添加到NSP列表中

    print("NSP数量:",len(nsp_list))

    endTimestamp = time.time()
    # print(endTimestamp)
    local_time = time.localtime(endTimestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(formatted_time)
    # 输出时间和空间情况
    print("Total Time:" + str((endTimestamp - startTimestamp) * 1000) + " ms")
    print("Max Memory:" + str(maxMemory) + " MB")

    """
    print("正序列模式（PSP）:")
    for psp in psp_list:
        print(psp)

    print("\n负序列模式（NSP）:")
    for nsp in nsp_list:
        print(nsp)
    """

    # print_patterns("PSP", psp_list)
    # print_patterns("NSP", nsp_list)