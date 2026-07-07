import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import csv
import pandas as pd
# Function to count the number of distinct prime factors
def count_distinct_prime_factors(n):
    factors = set()
    while n % 2 == 0:
        factors.add(2)
        n //= 2
    i = 3
    while i * i <= n:
        while n % i == 0:
            factors.add(i)
            n //= i
        i += 2
    if n > 1:
        factors.add(n)
    return len(factors)

def is_prime(n):
    """检测n是否为素数，更高效的方法"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def L(n, S):
    """根据n阶方的n值与n阶幻方的线和值S计算Level值L"""
    return 1.5 - ((n ** 2) / 2) + S / n

def is_valid(S):
    """注意这里要修改检查S是否有至少3个不同的质因数。"""
    return count_distinct_prime_factors(S) >= 1

def filter_S_l(start, end):
    """注意这里要修改检查S线和值是否是45的倍数），因此会过滤一些线和值。"""
    S_l = [S for S in range(start, end) if S % 1 == 0 and is_valid(S)]
    return S_l

# 并行化处理基于4核为主的8GB内存mac电脑
def S_l_list(start, end, chunk_size):
    # 分割线和值为多个子范围，每个子范围包含chunk_size个元素，最后返回S_l这个线和值list
    ranges = [(i, min(i + chunk_size, end)) for i in range(start, end, chunk_size)]
    S_l = []

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(filter_S_l, r[0], r[1]) for r in ranges]
        for future in concurrent.futures.as_completed(futures):
            S_l.extend(future.result())
    return S_l

def process_S(S, S_l_kids_range):
    """Feedback the results for specific S_l_kids_range in the form [kids_len, S, max_n, sum_n_squared]."""
    n = 1
    results = []

    while True:
        l_value = L(n, S)
        if l_value <= 0:
            break
        if l_value > 0 and l_value.is_integer():
            results.append((n, int(l_value)))
        n += 1
    kids_len = len(results)
    if kids_len in S_l_kids_range:
        max_n = results[-1][0] if results else None
        min_n = results[0][0] if results else None  # Get the smallest n value from results
        sum_n_squared = sum(n ** 2 for n, _ in results)
        prime_n_count = sum(1 for n, _ in results if is_prime(n))
        S_l_kids_range.remove(kids_len)
        factors_count = count_distinct_prime_factors(S)
        # Include min_n in the returned list
        return [kids_len, S, min_n, max_n, sum_n_squared, factors_count, prime_n_count]
    return None

def S_l_list(start, end, chunk_size):
    ranges = [(i, min(i + chunk_size, end)) for i in range(start, end, chunk_size)]
    S_l = []

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(filter_S_l, r[0], r[1]) for r in ranges]
        for future in as_completed(futures):
            S_l.extend(future.result())
    return S_l


def output_result_tofile(S_l, S_l_kids_lens, output_file):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['子幻方数量', '线和', '最小子阶n', '最大子阶n', 'n平方和', '线和的质因数种数', '线和对应素数n阶幻方个数'])
        for S in S_l:
            result = process_S(S, S_l_kids_lens)
            if result:
                writer.writerow(result)  # 将每个结果写入 CSV 文件中

def main():
    start_time = time.time()
    start=1
    end=100000
    chunk_size = (end-start)//20   #需要chunk_size为整数，使用整数除法//来向下取整，把S_l列表为成100份
    S_l_kids_lens = list(range(1, 50))  #子阶幻方数量范围从8个到321个
    output_file = "output4.csv"
    # 一次性计算所有S_l
    S_l = S_l_list(start, end, chunk_size)
    # 使用S_l进行其他计算
    output_result_tofile(S_l, S_l_kids_lens, output_file)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
if __name__ == "__main__":
    main()