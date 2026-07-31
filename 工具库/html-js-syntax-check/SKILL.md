---
name: html-js-syntax-check
description: "After every Edit/Write to .html files containing <script> blocks, automatically validate that JavaScript braces ({}) are balanced to prevent silent UI failures."
agent_created: true
---

# HTML/JS 三层验证（语法 → 解析 → 数据完整性）

## Purpose

修改任何生成 JS 代码的 `.py` 源文件（`sunburst_html.py` / `chakra_ann_table.py` / `reports_energy.py` 等）后，必须执行三层验证确保不会"语法正确但运行时炸"。

## Layer 1: Brace Balance（已有）

```python
import re
with open('PATH_TO_HTML', encoding='utf-8') as f:
    content = f.read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
for i, s in enumerate(scripts):
    opens = s.count('{')
    closes = s.count('}')
    diff = opens - closes
    if diff != 0:
        print(f'❌ SCRIPT BLOCK {i}: {opens} {{, {closes} }} (diff={diff})')
    else:
        print(f'✅ Script block {i}: braces balanced ({opens})')
```

## Layer 2: `node --check`（新增 — 铁律 45）

Brace balance 不足以捕获所有语法错误（如 f-string 内 `'` 提前闭合 JS 字符串）。`node --check` 是权威的 JS 解析器验证：

```bash
python -c "
import re, subprocess, tempfile, os
with open(r'OUTPUT_HTML', 'r', encoding='utf-8') as f:
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', f.read(), re.DOTALL)
if scripts:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as tf:
        tf.write(scripts[0]); tp = tf.name
    r = subprocess.run(['node', '--check', tp], capture_output=True, text=True, timeout=30)
    os.unlink(tp)
    if r.returncode == 0: print('✅ node --check passed')
    else: print('❌ node --check FAILED:', r.stderr[:500])
"
```

## Layer 3: 数据 Pipeline 字段完整性检查（新增 — 铁律 61）

**这是本轮 bug 暴露的盲区**：JS 语法正确、node --check 通过，但运行时 `undefined.toFixed()` 抛 TypeError → canvas 环可见但无标签，右列不更新。

### 检查步骤

在修改 `mergeSunburstData` 等数据汇总函数后：

1. **grep 所有下游消费者的字段引用**：
   ```bash
   grep -n "\.toFixed\(" OUTPUT_HTML
   grep -n "\.dev_pct\|\.dev5\|\.balance\|\.z_score" OUTPUT_HTML
   ```

2. **确认 pipeline 返回对象包含所有被引用字段**。如果 `mergeSunburstData` 返回 `{name,value,color,element}` 但下游有 `m.dev5.toFixed()` → 必须补充 `dev5` 到返回值。

3. **agent-browser 点击测试**（铁律 61 验证）：
   ```bash
   agent-browser open "file:///PATH_TO_HTML"
   agent-browser eval "typeof mergeSunburstData"  # 确认函数存在
   agent-browser eval "var d=mergeSunburstData(N-7,N); JSON.stringify(d.meridians[0])"  # 查看字段
   agent-browser click "#liteToggle"  # 测试切换
   agent-browser eval "document.getElementById('sunburst-summary')._sectors.length"  # 22=正常
   agent-browser close
   ```

### 典型缺陷模式

| 症状 | 根因 |
|------|------|
| Canvas 环可见、无文字标签 | `mergeSunburstData` 缺 `dev5` → Layer 5 `p.dev5.toFixed(1)` TypeError → 被 try-catch 吞 → labelQueue 跳过 |
| 右列文字不变 | `mergeSunburstData` 缺 `balance` → `buildLiteAnalysis` 中 `bal.toFixed(1)` TypeError |

### 预防规则

- 修改任何 JS 数据 pipeline 函数后 → `grep "\.toFixed\("` 核对字段
- f-string 源码中出现的 `{{`/`}}` 不是唯一关注点——生成后 JS 的实际括号平衡才是（Layer 1+2 联合检查）
- 宁可在 pipeline 末尾多补字段，也不要让下游消费者自己去判断 `undefined`

## Common Causes of Imbalance

| Cause | Fix |
|-------|-----|
| Removed function signature (`function foo() {`) but left body | Delete the entire function block (sig + body + closing `}`) |
| Removed function body but left opening or closing brace | Use line-number-based deletion to remove complete blocks |
| Template literal contains `{` or `}` | These are fine — but verify manually if the count is off by 1-2 |
| Extra `}` at end of file from partial cleanup | Check the last function before `// ========== Init ==========` |

## Fix Strategy

1. **Count the diff**: `diff > 0` = too many `{`, `diff < 0` = too many `}`
2. **Find approximate line**: Walk lines cumulatively
3. **For diff < 0 (extra `}`)**: Look for orphaned function bodies where the opening `{` was deleted but the closing `}` remains
4. **For diff > 0 (extra `{`)**: Look for a function that's missing its closing `}` — add one before `</script>`
