---
name: obsidian-graph-sync
description: >-
  One-command Obsidian vault graph network sync. Trigger when the user says
  "更新图谱", "sync graph", "刷新关系网", or any command to update the
  Obsidian knowledge graph connectivity.
  触发词：更新图谱、刷新关系网、sync graph、补链接、更新连接、修补图谱。
agent_created: true
---

# Obsidian Graph Sync — 一句话更新图谱网络

## 触发词

用户说以下任意一个：

- **更新图谱** / **刷新关系网** / **sync graph**
- **补链接** / **修补图谱** / **更新连接**

## 自动执行的 5 步流程

### Step 1：扫描 vault 全貌

```bash
# 统计当前状态
find "D:/knowledge-vault" -name "*.md" -not -path "*/.obsidian/*" -not -path "*/templates/*" | wc -l
```

### Step 2：检查异常（孤岛/无 cluster/无 wikilink）

```bash
# 无 cluster 的笔记
for f in D:/knowledge-vault/wiki/concepts/*.md D:/knowledge-vault/wiki/sources/*.md D:/knowledge-vault/wiki/syntheses/*.md; do
  [ -f "$f" ] || continue
  grep -q "^cluster:" "$f" || echo "NO_CLUSTER: $(basename $f .md)"
done

# wikilink 密度最低的笔记（出链 + 入链 < 3）
for f in D:/knowledge-vault/wiki/concepts/*.md D:/knowledge-vault/wiki/sources/*.md; do
  [ -f "$f" ] || continue
  bn=$(basename "$f" .md)
  out=$(grep -c '\[\[' "$f" 2>/dev/null)
  in=$(grep -rl "\[\[$bn\]\]" D:/knowledge-vault/wiki/ 2>/dev/null | wc -l)
  total=$((out + in))
  [ "$total" -lt 3 ] && echo "ISOLATED (links=$total): $bn"
done
```

### Step 3：自动分类（未分类笔记 → 匹配集群）

内容关键词匹配表：

| 关键词 | → cluster |
|--------|----------|
| `PKS\|千禧\|a·b=1\|双曲锥\|蛋形\|Schauberger\|波纹盘\|螺旋管\|黄金比\|白银比\|3-4-5` | `pks-geometry` |
| `Chudnovsky\|π\|pi\|模形式\|1728\|12进制\|Heegner\|黑洞\|T⁴` | `pi-number-theory` |
| `九宫格\|慈海\|白阳\|大同\|宇宙观\|天地图卷\|法盘` | `jiugongge-cosmology` |
| `NLS\|Mandelbrot\|分形\|EEQT\|驻波\|MWO\|频率映射\|细胞` | `nls-fractal` |
| `Kathara\|音频\|Lambdoma\|音光\|水分子\|1820\|商高\|频率` | `kathara-audio` |
| `GDV\|五行\|三因\|脉轮\|命理\|bio-well\|报告` | `gdv-health` |
| `Python\|编程\|bat\|铁律\|代码\|Windows` | `programming-tools` |

规则：匹配到 ≥2 个关键词 → 自动分配 cluster。匹配 ≤1 个 → 标记为 `?unclassified`，列出给用户确认。

### Step 4：修补缺失链接（双向 wikilink）

核心规则：
- **同 cluster 内的笔记必须互链**（成员↔hub）
- **跨 cluster 的 hub 必须互链**（PKS↔NLS, PKS↔九宫格, PKS↔Kathara, PKS↔π）
- **每篇笔记至少 2 个出链、2 个入链**

修补方式：
1. 更新 YAML `related:` 字段（Obsidian Graph View 识别）
2. 在正文"参见"部分追加 `[[wikilink]]`
3. 每条链接附一句话"为什么连"

### Step 5：汇报变更

输出格式：

```
📊 图谱同步完成

🔧 新增 cluster: X 篇
🔗 新增 wikilink: Y 条
🟢 已连通集群: A↔B(新增), C↔D(新增)
🔴 仍孤立的集群: E（需手动建立 Connection Note）
```

**若新增 wikilink > 10 条，用表格列出关键变更。**

---

## 调用方式

以后用户只需说：

```
更新图谱
```

系统自动执行 Step 1→5，无需用户指定任何参数。

若发现异常（某篇笔记分类模糊、某条连接不确定），用一句话询问用户确认，不中断流程。
