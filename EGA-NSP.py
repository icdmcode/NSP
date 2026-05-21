import random
from copy import deepcopy
import time
import psutil
import csv
import ast
import math
# 增加字段大小限制
csv.field_size_limit(2**31 - 1)


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


# 模式是否符合定义判断
def isLegal(pattern):
    if len(pattern) >= 3:
        if str(pattern[0]).startswith('¬') or str(pattern[len(pattern) - 1]).startswith('¬'):
            return False
    # 判断模式是否有连续两个负元素
    has_consecutive_neg = False
    for i in range(len(pattern) - 1):
        if str(pattern[i]).startswith('¬') and str(pattern[i + 1]).startswith('¬'):
            has_consecutive_neg = True
            break
    if has_consecutive_neg:
        return False
    return True


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
def calculate_support(pattern, dataset_size):
    if isLegal(pattern)==False:
        return 0
    # psp_support_dict = {tuple(tuple(item) for item in psp.pattern): psp.support for psp in psp_list}
    # psp_supsid_dict = {tuple(tuple(item) for item in psp.pattern): psp.sid_list for psp in psp_list}  # 补充

    nsc = [itemset[:] for itemset in pattern] # 注意创建拷贝，这里修改了一下
    # print("调试NSC")
    # print("nsc",nsc)

    # 提取 NSC 中的否定项，只有当存在否定项时才添加
    flag = 0 # 记录是否有连续两个负元素
    negated_items = []
    for itemset in nsc:
        negated_items_in_itemset = [item for item in itemset if item.startswith('¬')]
        # print("negated_items_in_itemset",negated_items_in_itemset)
        if negated_items_in_itemset:  # 只有当存在否定项时才添加
            flag += 1
            # print("flag",flag)
            if flag == 2:
                return 0
            negated_items.append(negated_items_in_itemset)
        else:
            flag = 0

    # print("调试negated_items")
    # print("执行到negated_items",negated_items)

    # （这里加上，如果不存在否定项，即全为正项，则直接返回）
    # 注意应该返回的是它们的PSP支持度（如果有），否则才返回0，不然会造成错误！
    # print("pattern:",pattern)
    if(len(negated_items)==0):
        support = psp_support_dict.get(tuple(tuple(item) for item in nsc), 0)  # 如果pattern不在字典中，返回0
        # print("support:", support)
        return support

    # positive_partner（即去掉nsc中所有的¬符号）
    nsc1 = [itemset[:] for itemset in nsc] # 注意创建拷贝
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
    if len(nsc) == 1:
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

    # print(nsc_support)
    return nsc_support


# 定义个体类，表示遗传算法中的染色体
class Individual:
    def __init__(self, sequence):
        self.sequence = sequence
        self.support = calculate_support(self.sequence, len_dataset)
        self.fitness = self.support  # 适应度目前设置为等于支持度

    # 计算个体的支持度
    # def calculate_support(self, dataset_size):
    #     self.support = calculate_support(self, dataset_size)
    #     self.fitness = self.support  # 适应度等于支持度

    # 变异函数
    def mutate(self, mutation_rate):
        # 随机选择序列中的项集进行变异
        for itemset in self.sequence:
            if random.random() < mutation_rate:
                # 目前采用随机选择一个项进行肯定和否定的转换
                # print("变异")
                random_item = random.choice(itemset)
                if random_item.startswith('¬'):
                    random_item = random_item[1:]
                else:
                    random_item = '¬' + random_item[1:]
        # calculate_support(self, len(dataset))
        self.support = calculate_support(self.sequence, len(dataset))
        self.fitness = self.support  # 适应度目前设置为等于支持度

    def __repr__(self):
        # return str(self.sequence)
        return f"Sequence: {self.sequence}, Support: {self.support}"


# 交叉函数
def crossover(parent1, parent2, crossover_rate):
    # 特殊情况处理，如果交叉点在开头或末尾，进行特殊的交叉操作
    crossover_point = random.randint(0, len(parent1.sequence))
    if crossover_point == 0 or crossover_point == len(parent1.sequence):
        # 进行特殊的交叉操作
        parent1.sequence, parent2.sequence = special_crossover(parent1.sequence, parent2.sequence)
    else:
        # 正常交叉操作：交换两个个体的序列从交叉点开始的部分
        parent1.sequence, parent2.sequence = (
            parent1.sequence[:crossover_point] + parent2.sequence[crossover_point:],
            parent2.sequence[:crossover_point] + parent1.sequence[crossover_point:]
        )
    # 重新计算子代的支持度
    parent1.support = calculate_support(parent1.sequence, len(dataset))
    parent2.support = calculate_support(parent2.sequence, len(dataset))
    # print(parent1.support)
    # print(parent2.support)
    return parent1, parent2


# 特殊情况下的交叉操作（交叉点在序列的开头或末尾）
def special_crossover(seq1, seq2):
    # crossover_point == 0 or crossover_point == len(parent1.sequence) 分别表示交叉点在开头或结尾
    """
    parent1:[['a'], ['a', 'b']]和parent2:[['d']]交叉
    如果crossover_point=0或2，返回的是[['a'], ['a', 'b'], ['d']]和[['d'], ['a'], ['a', 'b']]
    如果crossover_point=1则正常调用上面的普通crossover函数
    """
    # 将 parent2 的序列添加到 parent1 的末尾，反之亦然
    new_seq1 = seq1 + seq2
    new_seq2 = seq2 + seq1

    # 创建新的个体并返回
    return new_seq1, new_seq2


# 遗传算法
def genetic_algorithm(psp_list, min_sup, population_size=500, num_generations=100, mutation_rate=0.05, crossover_rate=0.6, k=50):
    global maxMemory, startTimestamp, endTimestamp, Flag
    global run_time, tot_time, tot_memo, tot_nsps
    Flag = 0
    maxMemory = 0
    # 多次实验取平均值
    # run_time = 0
    # tot_time = 0
    # tot_memo = 0
    # tot_nsps = 0
    startTimestamp = time.time()  # 记录算法开始时间
    # print("startTimestamp",startTimestamp)
    local_time = time.localtime(startTimestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(formatted_time)
    # 种群初始化是通过数据集生成所有长度为1的模式，并将它们对应的负模式也加进来
    # 例如对于这里的数据集，初始种群应为如下这些
    # [['a']], [['b']], [['c']], [['d']], [['a', 'b']], [['a', 'e']]
    # 并将他们对应的负模式也加进来，包括下面这些
    # [['¬a']], [['¬b']], [['¬c']], [['¬d']], [['¬a', '¬b']], [['¬a', '¬e']]
    # 初始化种群
    population = []
    # 生成所有长度为1的模式和它们对应的负模式
    for item in psp_list:
        for itemset in item.pattern: # 务必注意细节！
            population.append(Individual([itemset]))
            negated_itemset = ['¬' + item for item in itemset]
            population.append(Individual([negated_itemset]))
    # 注意这里要去重（策略可根据实际情况继续完善）
    # temp_population = population.copy()
    remove_duplicates_and_invalid_supports(population, len(dataset))
    # population = temp_population.copy()
    # 测试：输出初始化种群
    # print("输出初始化种群")
    # print(population)
    print("初始化种群大小",len(population))
    # print(population)

    # 这里不同于常规的遗传算法，我们采用增量种群，所有个体全都保留在新种群当中
    new_population = population # 注意是否使用.copy()不一样

    # 选择操作：选择支持度最高的k个个体
    def select_top_k(population, k):
        # return sorted(population, key=lambda x: x.fitness, reverse=True)[:k]
        return sorted(population, key=lambda x: x.fitness, reverse=True)[:len(population) * k // 100]

    for _ in range(num_generations):
        # print("种群代数：",_+1)
        # 选择和繁殖
        # 每次仅选择种群中支持度top k的个体进行后续操作
        topk_population = select_top_k(new_population, k)
        if(_ == 0):
            topk_population = new_population
        for _1 in range(k//2):
            parent1, parent2 = random.sample(topk_population, 2)
            # 创建父代个体的深拷贝以进行交叉和变异操作
            parent1_copy = deepcopy(parent1)
            parent2_copy = deepcopy(parent2)
            # 交叉
            crossover_rate = random.random()
            child1, child2 = crossover(parent1_copy, parent2_copy, crossover_rate)

            # 变异
            child1.mutate(mutation_rate)
            child2.mutate(mutation_rate)
            # 测试输出
            # print("parents:")
            # print(parent1)
            # print(parent2)
            # print("childs:")
            # print(child1)
            # print(child2)
            # new_population.extend([child1, child2])
            if (child1.support >= min_sup):
                new_population.extend([child1])
            if (child2.support >= min_sup):
                new_population.extend([child2])
        # print(_, len(population))
        # population = new_population # 不使用.copy()时二者是同一个对象
        # remove_duplicates_and_invalid_supports(new_population, len(dataset))
        # 这里目前采用中间过程不去重，仅个别模式重复出现，在中间过程可以被重复选择
        # print(_, len(population))

    # 这里并不只返回一个个体，将所有个体存储到一个全局列表当中（按照适应度函数从高到低排序），最后直接在main函数当中自行输出需要的前n个个体
    population.sort(key=lambda x: x.fitness, reverse=True)
    # 存储所有个体到全局列表
    global all_individuals
    all_individuals = population
    # 去掉重复个体以及加入剪枝策略（具体有待进一步修改）
    Flag = 1
    remove_duplicates_and_invalid_supports(all_individuals, len(dataset))
    checkMemory()
    endTimestamp = time.time() # 记录算法结束时间
    # print("endTimestamp",endTimestamp)
    local_time = time.localtime(endTimestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(formatted_time)
    tot_time += endTimestamp - startTimestamp
    tot_memo += maxMemory
    tot_nsps += len(all_individuals)


def remove_duplicates_and_invalid_supports(all_individuals, dataset_size):
    # 创建一个集合来存储已经遇到的个体的序列的元组表示（元组是不可变类型，适合作为集合的元素）
    seen_sequences = set()
    # 创建一个列表来存储去重后的个体
    unique_individuals = []

    for individual in all_individuals:
        if isLegal(individual.sequence) == False:
            continue
        # 将个体的序列转换成元组，以便进行比较和去重
        sequence_tuple = tuple(tuple(itemset) for itemset in individual.sequence)

        # 检查当前个体是否已经出现过，如果没有，则添加到unique_individuals列表
        if sequence_tuple not in seen_sequences:
            # 同时检查支持度是否不等于数据库最大正序列长度
            if Flag == 0:
                if len(individual.sequence) <= max_length:
                    unique_individuals.append(individual)
                    seen_sequences.add(sequence_tuple)  # 将新的个体序列的元组表示添加到集合中
            else:
                if len(individual.sequence) <= max_length and individual.support <= dataset_size and individual.support >=min_sup:
                    unique_individuals.append(individual)
                    seen_sequences.add(sequence_tuple)  # 将新的个体序列的元组表示添加到集合中

    # 更新all_individuals为去重后的个体列表
    all_individuals[:] = unique_individuals  # 使用[:]来更新列表的引用


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


# 主函数
if __name__ == "__main__":
    global all_individuals, min_sup, run_time, len_dataset
    global run_time, tot_time, tot_memo, tot_nsps
    # 多次实验取平均值
    run_time = 0
    tot_time = 0
    tot_memo = 0
    tot_nsps = 0
    # 输入数据集（这里以这个数据集为例）
    """
    dataset = [
        [['a'], ['b'], ['c']],
        [['a'], ['a', 'b']],
        [['a', 'e'], ['a', 'b'], ['c']],
        [['a'], ['a']],
        [['d']]
    ]
    """

    file_path = 'datasets/test.txt'
    dataset = read(file_path)
    len_dataset = len(dataset)
    # 计算dataset中序列的最大长度和最小长度
    max_length = max(len(sequence) for sequence in dataset) if dataset else 0
    min_length = min(len(sequence) for sequence in dataset) if dataset else 0
    print("最大长度:", max_length)
    print("最小长度:", min_length)

    """
    psp_list = [
        SequentialPattern([['a']], 4, [1, 2, 3, 4]),
        SequentialPattern([['b']], 3, [1, 2, 3]),
        SequentialPattern([['c']], 2, [1, 3]),
        SequentialPattern([['a'], ['a']], 3, [2, 3, 4]),
        SequentialPattern([['a'], ['b']], 3, [1, 2, 3]),
        SequentialPattern([['a'], ['c']], 2, [1, 3]),
        SequentialPattern([['b'], ['c']], 2, [1, 3]),
        SequentialPattern([['a', 'b']], 2, [2, 3]),
        SequentialPattern([['a'], ['b'], ['c']], 2, [1, 3]),
        SequentialPattern([['a'], ['a', 'b']], 2, [2, 3])
    ]
    """

    file_path = 'test/psp_list_test_0.4.csv'
    psp_list = read_patterns_from_csv(file_path)  # 通过csv文件读入
    # print(psp_list)

    # psp_support_dict = {tuple(tuple(item) for item in psp.pattern): psp.support for psp in psp_list}
    # print(psp_support_dict)
    # 模块级变量
    psp_support_dict = {tuple(tuple(item) for item in psp.pattern): psp.support for psp in psp_list}
    psp_supsid_dict = {tuple(tuple(item) for item in psp.pattern): psp.sid_list for psp in psp_list}  # 补充

    all_individuals = []  # 初始化种群的全局列表
    # min_sup = 2  # 设置最小支持度阈值
    min_sup = math.ceil(len(dataset) * 0.4)  # 向上取整


    # 单次运行
    """
    genetic_algorithm(psp_list, min_sup) # 运行遗传算法

    # 输出按照适应度从高到低排序的所有个体
    for individual in all_individuals:
        print(f"Sequence: {individual.sequence}, Support: {individual.support}, Fitness: {individual.fitness}")

    # 输出时间和空间情况
    print(" Total time ~ " + str((endTimestamp - startTimestamp) * 1000) + " ms")
    print(" Memory ~ " + str(maxMemory) + " MB")
    print(len(all_individuals))
    """

    # 多次运行取平均值
    run_time = 10
    for _ in range(run_time):
        all_individuals = []  # 初始化种群的全局列表
        genetic_algorithm(psp_list, min_sup)  # 运行遗传算法
    print("time:",tot_time*1000/run_time)
    print("memory:",tot_memo/run_time)
    print("NSP:",tot_nsps/run_time)