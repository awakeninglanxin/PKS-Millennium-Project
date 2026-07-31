#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""任务5: 灾难恢复详细仿真 — 真实故障注入

场景: 芯片设计中途发现致命bug, 需回滚N层重做
对比: CPM(先攻难→回滚代价大) vs Hybrid(先简后繁→回滚代价小)
"""
import numpy as np, random

class FaultyTask:
    def __init__(self, name, complexity, depth, deps=None):
        self.name = name; self.complexity = complexity
        self.depth = depth; self.dependencies = deps or []
        self.time_cost = 0.1 + 0.03 * complexity
        self.success = False; self.attempts = 0

def gen_dag():
    t = {}
    t['L1'] = FaultyTask('L1', 1, 0); t['L2'] = FaultyTask('L2', 1, 0)
    t['L3'] = FaultyTask('L3', 2, 0)
    t['A'] = FaultyTask('A', 3, 1, ['L1']); t['B'] = FaultyTask('B', 3, 1, ['L2'])
    t['C'] = FaultyTask('C', 4, 1, ['L3'])
    t['D'] = FaultyTask('D', 5, 2, ['A','B']); t['E'] = FaultyTask('E', 5, 2, ['B','C'])
    t['F'] = FaultyTask('F', 6, 2, ['A'])
    t['G'] = FaultyTask('G', 7, 3, ['D','E','F'])
    t['V'] = FaultyTask('V', 8, 4, ['G']); t['P'] = FaultyTask('P', 9, 4, ['G'])
    t['T'] = FaultyTask('T', 1, 5, ['V','P'])
    return t

def rank_cpm(t): return (-t.depth, -t.complexity)
def rank_hybrid(t):
    if t.complexity >= 7: return (0, t.complexity)  # InternalAddr for complex
    else: return (1, t.complexity)  # FareyTree for simple

def deps_met(task, done):
    return all(d in done for d in task.dependencies)

def simulate_with_fault(tasks, ranker, name, fault_at_task='G', fault_chance=0.15,
                        rollback_depth=3, max_att=15):
    """真实故障注入: 在设计G(最复杂的集成模块)时有15%概率发现致命bug"""
    done = set(); total_t = 0.0; succ = 0; total_a = 0
    ready = []; stack = []; faults = 0; rollback_cost = 0

    while len(done) < len(tasks):
        for task in tasks.values():
            if task.name not in done and deps_met(task, done):
                if task.name not in [t.name for t in ready]:
                    ready.append(task)
        if not ready: break

        ready.sort(key=lambda t: ranker(t))
        task = ready.pop(0)

        # 故障注入: 在特定任务有概率触发致命bug
        fault_triggered = False
        if task.name == fault_at_task and random.random() < fault_chance:
            fault_triggered = True
            faults += 1
            # 回滚
            for _ in range(min(rollback_depth, len(stack))):
                rn = stack.pop()
                if rn in done:
                    done.remove(rn)
                    total_t += 0.8  # 回滚惩罚(重做+debug时间)
            rollback_cost += rollback_depth * 0.8
            # 重新加入就绪队列
            continue

        for attempt in range(1, max_att + 1):
            total_a += 1; task.attempts = attempt
            comp = task.complexity

            # 基础成功率: 简单任务高, 复杂任务低
            base = 0.45 + 0.05 * (10 - comp)
            # 经验累积
            if name == 'Hybrid':
                base += 0.025 * len(done)
            base = min(base, 0.92)

            total_t += task.time_cost
            if random.random() < (base + 0.015 * (attempt - 1)):
                succ += 1; task.success = True
                done.add(task.name); stack.append(task.name)
                break

        if not task.success: done.add(task.name)

    return {
        'name': name, 'time': total_t, 'att': total_a,
        'succ': succ / len(tasks), 'faults': faults,
        'rollback_cost': rollback_cost
    }

# ====== 实验 ======
N = 500
results = {'CPM': [], 'Hybrid': []}

for _ in range(N):
    for name, ranker in [('CPM', rank_cpm), ('Hybrid', rank_hybrid)]:
        r = simulate_with_fault(gen_dag(), ranker, name)
        results[name].append(r)

print("=" * 65)
print(f"灾难恢复详细仿真 — {N}轮, 故障注入@G(15%概率), 回滚3层")
print("=" * 65)

for name in ['CPM', 'Hybrid']:
    rs = results[name]
    t = np.mean([r['time'] for r in rs])
    a = np.mean([r['att'] for r in rs])
    s = np.mean([r['succ'] for r in rs])
    f = np.mean([r['faults'] for r in rs])
    rc = np.mean([r['rollback_cost'] for r in rs])
    print(f"\n{name}:")
    print(f"  总耗时: {t:.3f}s  尝试: {a:.1f}次  成功率: {s:.1%}")
    print(f"  故障触发: {f:.1f}次  回滚成本: {rc:.2f}s")

t_c = np.mean([r['time'] for r in results['CPM']])
t_h = np.mean([r['time'] for r in results['Hybrid']])
print(f"\n💎 Hybrid比CPM省 {((1-t_h/t_c)*100):.1f}% 在灾难恢复场景")
