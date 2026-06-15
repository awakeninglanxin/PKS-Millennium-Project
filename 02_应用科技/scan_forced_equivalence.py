# 铁律58自动化检查 — 扫描项目MD中"强行等价"模式
# 输出待人工复核的候选清单

import os
import re
import sys

PROJECT_ROOT = r"D:\AAA我的文件\PKS_千禧难题_统一解"

# 可疑模式 + 对应的严重度
PATTERNS = [
    # 高严重度: 明确声称等价、统一、精确对应
    (r"✅.*等价", "HIGH", "✅等价断言"),
    (r"完全等价", "HIGH", "完全等价声明"),
    (r"精确对应", "HIGH", "精确对应声明"),
    (r"完美统一", "HIGH", "完美统一声明"),
    (r"完美对应", "HIGH", "完美对应声明"),
    (r"两者.*(相同|一致).*形状", "HIGH", "两者形状相同声明"),
    (r"同一物理.*(语言|表达)", "HIGH", "同一物理的两种语言"),
    (r"100%[的之]?.{0,5}同构", "HIGH", "100%同构标记"),
    (r"✅\s*\d{2,3}%", "HIGH", "百分数✅标记"),
    # 中严重度: 暗示性的强关联
    (r"无缝.*对[应接]", "MEDIUM", "无缝对接"),
    (r"等价于", "MEDIUM", "等价于声明"),
    (r"就是.{0,5}的.{0,5}几何", "MEDIUM", "X就是Y的几何"),
    (r"直接.*映射", "MEDIUM", "直接映射声明"),
    # 低严重度: 可能无害但值得标注
    (r"精确.*一致", "LOW", "精确一致声明"),
    (r"严格.*对应", "LOW", "严格对应声明"),
]

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "images", "相关图片", "Eyes + Ears = IDEAS"}
EXCLUDE_FILES = {"铁律58", "MEMORY.md"}  # 不扫自身和铁律文件

def scan_file(filepath):
    """扫描单个文件"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
    
    findings = []
    for i, line in enumerate(lines, 1):
        for pattern, severity, label in PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # 跳过被修正标记包围的行
                if '修正' in line and ('v1.0' in line or '已删除' in line or '错误' in line):
                    continue
                context = line.strip()[:120]
                findings.append((i, severity, label, context, match.group()))
                break  # 每行只匹配最高优先级的
    return findings

def main():
    results = {"HIGH": [], "MEDIUM": [], "LOW": []}
    file_count = 0
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        
        for fname in files:
            if not fname.endswith('.md'):
                continue
            if any(excl in fname for excl in EXCLUDE_FILES):
                continue
            
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, PROJECT_ROOT)
            
            findings = scan_file(fpath)
            if findings:
                file_count += 1
                for lineno, severity, label, context, matched in findings:
                    results[severity].append((relpath, lineno, label, context, matched))
    
    # 输出报告
    print("=" * 70)
    print("铁律58 自动化扫描 — 已修复文件不应出现在HIGH列表中")
    print(f"扫描范围: {PROJECT_ROOT}")
    print(f"命中文件数: {file_count}")
    print("=" * 70)
    
    total = sum(len(v) for v in results.values())
    
    for severity in ["HIGH", "MEDIUM", "LOW"]:
        items = results[severity]
        if not items:
            continue
        print(f"\n{'='*70}")
        print(f"  [{severity}] — {len(items)} 条")
        print(f"{'='*70}")
        for relpath, lineno, label, context, _ in items[:30]:
            print(f"  {relpath}:{lineno} [{label}]")
            print(f"    {context}")
    
    print(f"\n{'='*70}")
    print(f"总计: HIGH={len(results['HIGH'])} MEDIUM={len(results['MEDIUM'])} LOW={len(results['LOW'])}")
    print(f"待人工复核: {total} 条")
    
    if len(results['HIGH']) == 0:
        print("\n[✓] 无 HIGH 级别命中 — 铁律58清理有效")
    else:
        print(f"\n[!] {len(results['HIGH'])} 条 HIGH 级别命中 — 需立即复核")
        for relpath, lineno, label, context, _ in results['HIGH'][:10]:
            print(f"  [!] {relpath}:{lineno} [{label}]")

if __name__ == "__main__":
    main()
