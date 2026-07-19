#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenROAD Hybrid Scheduler Plugin — FareyTree + InternalAddr 自适应调度

用法:
  openroad -python hybrid_scheduler.py -script your_flow.tcl

输入: OpenROAD 的 sta (时序分析) 输出 JSON
输出: 重排序后的 task execution order

集成点:
  1. 读取 OpenROAD timing report → 提取关键路径
  2. 将关键路径映射为 Farey 复杂度 (period)
  3. Hybrid 调度重排 task 执行顺序
  4. 写回 OpenROAD 约束文件
"""

import json, sys, os, math
from collections import defaultdict
from math import gcd

# ====== Hybrid 调度引擎 ======
class FareyHybridScheduler:
    """将 Farey 树 + 内地址 映射到 OpenROAD 的 task scheduling"""
    
    def __init__(self):
        self.task_graph = {}
        
    def load_timing_report(self, timing_json):
        """从 OpenROAD timing report 提取 task 图"""
        data = json.loads(timing_json) if isinstance(timing_json, str) else timing_json
        for node in data.get('nodes', []):
            name = node.get('name', f'node_{len(self.task_graph)}')
            slack = node.get('slack', 0)  # ps, 越小越紧急
            depth = node.get('logic_depth', 1)
            deps = node.get('dependencies', [])
            
            # 映射 slack → Farey 复杂度
            # slack 越小(越紧急) → 复杂度越高
            if slack < -100:   complexity = 9  # 严重违规
            elif slack < -50:   complexity = 7
            elif slack < -20:   complexity = 5
            elif slack < 0:     complexity = 4
            elif slack < 50:    complexity = 2
            else:              complexity = 1  # 充分裕量
            
            self.task_graph[name] = {
                'name': name, 'complexity': complexity,
                'depth': depth, 'deps': deps,
                'slack': slack
            }
    
    def hybrid_rank(self, task_name):
        """Hybrid 排序: 复杂任务用 InternalAddr, 简单用 FareyTree"""
        task = self.task_graph[task_name]
        comp = task['complexity']
        
        if comp >= 7:
            # InternalAddr: 分岔深度
            n, val = 1, 1
            while val < comp: val *= 2; n += 1
            return (0, n, task['slack'])  # 优先队列
        else:
            # FareyTree: 分母深度
            return (1, max(1, comp - 2), task['slack'])
    
    def cpm_rank(self, task_name):
        """CPM: Critical Path Method (baseline)"""
        task = self.task_graph[task_name]
        return (-task['slack'], task['depth'])
    
    def schedule(self, method='hybrid'):
        """执行调度, 返回排序后的任务列表"""
        names = list(self.task_graph.keys())
        
        if method == 'hybrid':
            names.sort(key=lambda n: self.hybrid_rank(n))
        else:
            names.sort(key=lambda n: self.cpm_rank(n))
        
        schedule = []
        for name in names:
            t = self.task_graph[name]
            schedule.append({
                'name': name,
                'complexity': t['complexity'],
                'slack_ps': t['slack'],
                'depth': t['depth']
            })
        
        return schedule
    
    def export_openroad_sdc(self, schedule, output_path):
        """导出为 OpenROAD SDC 约束文件"""
        lines = ['# Hybrid Farey Scheduler — Auto-generated SDC constraints',
                 f'# Method: FareyTree + InternalAddr hybrid',
                 f'# Tasks: {len(schedule)}',
                 '# Ordered by: complexity <7 → FareyTree depth',
                 '#             complexity ≥7 → InternalAddr bifurcation depth',
                 '']
        
        for i, task in enumerate(schedule):
            # 按调度顺序设置 group_path 优先级
            priority = len(schedule) - i  # 越早调度优先级越高
            lines.append(f'# Rank {i+1}: {task["name"]} '
                        f'(complexity={task["complexity"]}, slack={task["slack_ps"]}ps)')
            lines.append(f'group_path -name {task["name"]}_grp '
                        f'-weight {priority:.1f} '
                        f'-priority {priority}')
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return output_path


# ====== 示例: 仿 OpenROAD timing report ======
if __name__ == '__main__':
    # 模拟一个典型设计的 timing report
    sample_report = {
        'design': 'RISC-V Core (仿 VerCore)',
        'nodes': [
            {'name': 'fetch',    'slack': 20,  'logic_depth': 2, 'dependencies': []},
            {'name': 'decode',   'slack': 15,  'logic_depth': 3, 'dependencies': ['fetch']},
            {'name': 'execute',  'slack': -30, 'logic_depth': 4, 'dependencies': ['decode']},
            {'name': 'memory',   'slack': -80, 'logic_depth': 5, 'dependencies': ['execute']},
            {'name': 'writeback','slack': 10,  'logic_depth': 6, 'dependencies': ['memory']},
            {'name': 'branch',   'slack': -120,'logic_depth': 3, 'dependencies': ['decode']},
            {'name': 'mul_div',  'slack': -55, 'logic_depth': 8, 'dependencies': ['execute']},
            {'name': 'csr',      'slack': 40,  'logic_depth': 2, 'dependencies': ['decode']},
        ]
    }
    
    sched = FareyHybridScheduler()
    sched.load_timing_report(sample_report)
    
    print("=" * 55)
    print("Hybrid Farey Scheduler — OpenROAD Plugin Demo")
    print("=" * 55)
    
    # Hybrid 调度
    hyb = sched.schedule('hybrid')
    print(f"\n{'Hybrid (Farey+InternalAddr)':<35} {'Complexity':>8}")
    print("-" * 45)
    for t in hyb:
        print(f"  {t['name']:<25} slack={t['slack_ps']:>5}ps  {t['complexity']:>3}")
    
    # CPM 调度 (对比)
    cpm = sched.schedule('cpm')
    print(f"\n{'CPM (baseline)':<35} {'Complexity':>8}")
    print("-" * 45)
    for t in cpm:
        print(f"  {t['name']:<25} slack={t['slack_ps']:>5}ps  {t['complexity']:>3}")
    
    # 导出 SDC
    outdir = os.path.dirname(os.path.abspath(__file__))
    hyb_sdc = os.path.join(outdir, 'hybrid_farey.sdc')
    cpm_sdc = os.path.join(outdir, 'cpm_baseline.sdc')
    
    sched.export_openroad_sdc(hyb, hyb_sdc)
    sched.export_openroad_sdc(cpm, cpm_sdc)
    
    print(f"\n✅ SDC files generated:")
    print(f"   {hyb_sdc}")
    print(f"   {cpm_sdc}")
    print(f"\n💡 To use in OpenROAD:")
    print(f"   openroad -python {__file__} -script your_design.tcl")
    print(f"   # then in your_design.tcl: source hybrid_farey.sdc")
