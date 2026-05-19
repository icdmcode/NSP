import sys
PLACE_HOLDER = '_' # 占位符
import csv
import time
import psutil
import math
startTimestamp = 0
endTimestamp = 0
maxMemory = 0
# sys.stdout = open('output1.txt', 'w', encoding='utf-8')

# 最新修正的读入方法（数字和字母都可以适用）
def read(filename):
    # 读取输入文件
    S = []
    with open(filename, 'r') as input:
        for line in input:
            # 移除行末的 '-2'
            line = line.strip().rstrip('-2')
            elements = line.split('-1')  # 序列中元素之间的分隔符，可以根据需要修改
            # print(elements)
            s = []
            for e in elements:
                # 将非空字符串分割成列表，确保元素内部的空格被正确处理
                if e.strip():
                    s.append(e.split())
            # print(s)
            S.append(s)
    print("输入数据集", filename)
    # print(S)
    return S


class sequencePattern:
    # 定义一个序列模式类，方便后续处理
    def __init__(self, sequence, support, sid_list=None):
        self.sequence = []
        for s in sequence:
            self.sequence.append(list(s))
        self.support = support
        self.size = len(self.sequence)  # 元素（项集）的数量（不是项的数量）
        self.sid_list = sid_list if sid_list else []

    def append(self, p):
        #如果第一位是‘_’，则去掉‘_’之后再加入到sequence里面
        if p.sequence[0][0] == PLACE_HOLDER:
            first_e = p.sequence[0]
            first_e.remove(PLACE_HOLDER)
            self.sequence[-1].extend(first_e)
            self.sequence.extend(p.sequence[1:])
        else:
            self.sequence.extend(p.sequence)
        self.support = min(self.support, p.support)
        self.size = len(self.sequence) # 注意这里要更新！
        # 当合并或扩展序列模式时，新模式的支持度不超过原模式的支持度


def prefixSpan(pattern, S, threshold):

    patterns = []
    f_list = frequent_items(S, pattern, threshold)

    for i in f_list:
        p = sequencePattern(pattern.sequence, pattern.support, i.sid_list)
        # print("p.sid_list:",p.sid_list)
        p.append(i)
        patterns.append(p)
        p_S = build_projected_database(S, p)
        p_patterns = prefixSpan(p, p_S, threshold) # 递归挖掘

        # 打印 p_patterns 以查看内容
        # print("当前递归挖掘得到的序列模式：")
        # for pp in p_patterns:
        #     print("pattern:", pp.sequence, ", support:", pp.support)

        patterns.extend(p_patterns)

    checkMemory()

    return patterns


def frequent_items(S, pattern, threshold):
    items = {}  # 用于存储整个序列数据库 S 中频繁出现的项及其计数
    _items = {}  # 用于存储在当前模式 pattern 之后频繁出现的项及其计数
    f_list = []  # 用于存储最终找到的频繁项的 sequencePattern 对象列表
    sequence_ids_items = {}  # 包含模式的序列id
    sequence_ids__items = {}  # 包含模式的序列id

    if S is None or len(S) == 0:
        return []

    if len(pattern.sequence) != 0:
        last_e = pattern.sequence[-1]
    else:
        last_e = []

    for idx, s in enumerate(S):
        if len(s) == 0: continue  # 这里要注意细节！
        is_prefix = True
        for item in last_e:
            if item not in s[0]:
                is_prefix = False
                break
        # print(is_prefix)
        if is_prefix and len(last_e) > 0:
            index = s[0].index(last_e[-1])
            if index < len(s[0]) - 1:
                for item in s[0][index + 1:]:
                    if item in _items:
                        # print("测试2")
                        # print(s)
                        _items[item] += 1
                    else:
                        _items[item] = 1
                        sequence_ids__items[item] = []
                    sequence_ids__items[item].append(idx + 1)
        # 有占位符_的情况
        if PLACE_HOLDER in s[0]:
            for item in s[0][1:]:
                if item in _items:
                    _items[item] += 1
                else:
                    _items[item] = 1
                    sequence_ids__items[item] = []
                sequence_ids__items[item].append(idx + 1)
            s = s[1:]
        # 从下一个项集开始
        counted = []
        for element in s:
            for item in element:
                if item not in counted:
                    counted.append(item)
                    if item in items:
                        items[item] += 1
                    else:
                        items[item] = 1
                        sequence_ids_items[item] = []
                    sequence_ids_items[item].append(idx + 1)

    # 最新：关于之前的错误，但是这样写并不能解决！
    # 更新 items，将 _items 中的项合并回 items
    # for k, v in _items.items():
    #     if k not in items:
    #         items[k] = 0
    #     items[k] += v

    # 创建 sequencePattern 对象并记录序列编号
    for k, v in items.items():
        # v += _items.get(k, 0)
        if v >= threshold:
            f_list.append(sequencePattern([[k]], v, sequence_ids_items.get(k, [])))
    for k, v in _items.items():
        if v >= threshold:
            f_list.append(sequencePattern([[PLACE_HOLDER, k]], v, sequence_ids__items.get(k, [])))

    # f_list.extend([sequencePattern([[PLACE_HOLDER, k]], v) for k, v in _items.items() if v >= threshold])
    # f_list.extend([sequencePattern([[k]], v) for k, v in items.items() if v >= threshold])

    # 注意这里不能排序！否则sid就错了！
    # sorted_list = sorted(f_list, key=lambda p: p.support)

    # 最新增加调试输出：查看数据库变化
    # print("当前投影数据库：")
    # for idx, s in enumerate(S):
    #     print(idx+1, s)

    # 打印 f_list 以查看内容 # 输出内容
    # print("当前频繁项列表：")
    # for p in f_list:
    #     print("pattern:", p.sequence, ", support:", p.support,", sid_list:", p.sid_list)

    checkMemory()
    return f_list


def build_projected_database(S, pattern):
    """
    # pattern是当前的前缀，S为其投影数据库
    print("投影数据库：")
    print(S)
    print(pattern.sequence)
    """
    p_S = []
    last_e = pattern.sequence[-1]
    last_item = last_e[-1]
    for s in S:
        p_s = []
        for element in s:
            is_prefix = False
            if PLACE_HOLDER in element:
                if last_item in element and len(pattern.sequence[-1]) > 1:
                    is_prefix = True
            else:
                is_prefix = True
                for item in last_e:
                    if item not in element:
                        is_prefix = False
                        break
            if is_prefix:
                e_index = s.index(element)
                i_index = element.index(last_item)
                if i_index == len(element) - 1:
                    p_s = s[e_index + 1:]
                else:
                    p_s = s[e_index:]
                    # index = element.index(last_item)
                    e = element[i_index:]
                    e[0] = PLACE_HOLDER
                    p_s[0] = e
                break

        # if len(p_s) != 0: # 这里不要省略，否则会影响序列编号！
        p_S.append(p_s)

    checkMemory()
    # print("数据库size:",len(p_S))
    return p_S


def save_patterns_to_csv(patterns, filename): # 文件保存操作
    patterns = sorted(patterns, key=lambda x: x.sequence)
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Pattern', 'Support', 'Size', 'SIDs'])  # 写入标题
        for p in patterns:
            pattern_str = '[' + ', '.join(['[' + ', '.join(item) + ']' for item in p.sequence]) + ']'
            sid_str = ','.join(map(str, p.sid_list))
            # print("Writing:", pattern_str, p.support, p.size, sid_str)  # 打印即将写入的内容
            writer.writerow([pattern_str, p.support, p.size, sid_str])


def print_patterns(patterns):
    print("输出结果")
    num_patterns = len(patterns)
    print(f"序列模式数量: {num_patterns}")
    """
    patterns = sorted(patterns, key=lambda x: x.sequence)
    for p in patterns:
        print(f"SequentialPattern({p.sequence}, {p.support}, {p.size}, {p.sid_list})")
    print(f"序列模式数量: {num_patterns}")
    """


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
    maxMemory = 0

    S = read("datasets/BMS1_4.txt")

    startTimestamp = time.time()
    # print(startTimestamp)
    local_time = time.localtime(startTimestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(formatted_time)

    patterns = prefixSpan(sequencePattern([], sys.maxsize), S, math.ceil(len(S)*0.005))
    endTimestamp = time.time()
    # print(endTimestamp)
    local_time = time.localtime(endTimestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(formatted_time)

    print_patterns(patterns) # 输出内容
    save_patterns_to_csv(patterns, "test/psp_list_BMS1_4_0.005.csv")  # 保存到csv文件

    # 输出时间和空间情况
    print("Total Time:" + str((endTimestamp - startTimestamp) * 1000) + " ms")
    print("Max Memory:" + str(maxMemory) + " MB")