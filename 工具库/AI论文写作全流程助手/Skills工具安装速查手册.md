# Skills 工具安装速查手册

> 🛠️ 已实测、活跃维护的 12 个 AI 科研 Skills，附安装命令。
> 来源：飞书《AI辅助科研工具大全》实测整理 + GitHub 社区

---

## 快速索引

| # | 工具 | 核心用途 | 安装复杂度 | 推荐指数 |
|---|------|----------|:--:|:--:|
| 1 | Nature Skills | 论文全流程 | ⭐ | ⭐⭐⭐⭐⭐ |
| 2 | ARS | 学术研究管道 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 3 | Nature Paper Skills | Journal-first 投稿 | ⭐⭐ | ⭐⭐⭐⭐ |
| 4 | Scientific Writing | IMRaD 结构化写作 | ⭐ | ⭐⭐⭐⭐⭐ |
| 5 | SciPilot Figure | 科研配图 | ⭐ | ⭐⭐⭐⭐ |
| 6 | K-Dense Scientific | 图表+Graphical Abstract | ⭐ | ⭐⭐⭐⭐ |
| 7 | thesis-writer | 中文论文 GB/T 7714 | ⭐ | ⭐⭐⭐⭐ |
| 8 | Cite Verify | 引文核验 | ⭐ | ⭐⭐⭐ |
| 9 | LaTeX Writer | LaTeX 排版 | ⭐ | ⭐⭐⭐ |
| 10 | Stats Sanity | 统计分析检查 | ⭐ | ⭐⭐⭐ |
| 11 | Paper RAG | 文献知识库 | ⭐⭐ | ⭐⭐⭐ |
| 12 | PaperSpine | 论文结构拆解 | ⭐ | ⭐⭐⭐ |

---

## 1. Nature Skills ⭐⭐⭐⭐⭐（必装）

**用途**：Nature 风格论文的全流程——润色、图表、引文检索、审稿回复、PPT、专利

**GitHub**: `Yuan1z0825/nature-skills`

**Claude Code 安装**：
```bash
claude plugin marketplace add Yuan1z0825/nature-skills
claude plugin install nature-skills
```

**Codex 安装**：
```
/plugin marketplace add Yuan1z0825/nature-skills
/plugin install nature-skills
```

**手动安装**：
```bash
git clone https://github.com/Yuan1z0825/nature-skills.git
# 复制整个 skill 目录（含 references/ assets/ 等依赖！）
cp -R nature-skills/skills/nature-* ~/.claude/skills/
```

**⚠️ 安装必须复制完整文件夹**，不要只复制 SKILL.md。否则会因缺少依赖而报错。

**常用命令**：
```
/nature-polish      → 学术语言润色
/nature-figure      → 生成 SVG 图表
/nature-citation    → 引文检索
/nature-rebuttal    → 审稿回复
/nature-ppt         → 论文转 PPT
```

---

## 2. ARS (Academic Research Skills) ⭐⭐⭐⭐⭐（必装）

**用途**：从研究→撰写→检查→评审→修改→复审→定稿的完整管道，带强制学术诚信闸门

**GitHub**: `Imbad0202/academic-research-skills`

**安装**：
```bash
# Claude Code
/plugin marketplace add Imbad0202/academic-research-skills
/plugin install academic-research-skills

# 手动安装
git clone https://github.com/Imbad0202/academic-research-skills.git
cp -R academic-research-skills/* ~/.claude/skills/
```

**工作流特点**：
- 每个阶段结束需要用户确认 checkpoint
- Stage 2.5 和 Stage 4.5 是**不可跳过的学术诚信闸门**
- 支持 Semantic Scholar API 验证引文
- Human-in-the-loop：AI 出建议，你最终决策

**常用命令**：
```
/ars-plan          → 苏格拉底式对话，帮你规划章节
/ars-lit-review    → 文献综述
/ars-write         → 论文撰写
/ars-audit         → 完整性检查
```

---

## 3. Nature Paper Skills ⭐⭐⭐⭐

**用途**：Nature 系列期刊专属的投稿全链路（Journal-first, claim-driven）

**GitHub**: `Boom5426/nature-paper-skills`

**核心理念**：
- Journal-first，不是通用论文写作
- Claim-driven，不是 panel-driven
- 一张主图只承载一个主结论
- 先修结构证据链，再做语句级润色

**安装（推荐让 AI 自己装）**：
```
把以下这段话直接发给 Claude Code 或 Codex：

"把当前仓库里的推荐 skills 安装到 ~/.claude/skills/: paper-workflow, paper-bootstrap, nature-portfolio-playbook, scientific-writing, manuscript-optimizer, results-section-revision, figure-planner, citation-verifier, data-availability, submission-audit, rebuttal-response。复制整个 skill 目录，不要只复制 SKILL.md。安装完成后，列出已安装目录，并用 paper-workflow 帮我判断当前稿件下一步该用哪个 skill。"
```

**包含的 Skills**：
- `paper-workflow` — 判断该用哪个 skill
- `paper-bootstrap` — 初始化论文项目
- `manuscript-optimizer` — 结构与证据链修复
- `results-section-revision` — Results 小节级修复
- `figure-planner` — 一图一主张
- `citation-verifier` — 引用卫生检查
- `submission-audit` — 投稿前总预检
- `rebuttal-response` — 审稿回复

---

## 4. Scientific Writing ⭐⭐⭐⭐⭐

**用途**：IMRAD 结构化写作 + APA/AMA/Vancouver/Chicago/IEEE 引文格式

**GitHub**: `K-Dense-AI/claude-scientific-skills`

**安装**：
```bash
# Claude Code
claude plugin marketplace add K-Dense-AI/claude-scientific-skills
claude plugin install scientific-skills
```

**核心规则**：绝不用 bullet points 写最终稿——先用 bullet points 做大纲，再转换成流畅段落。

**⚠️ 必须配合 graphical abstract**：每篇论文必须生成 Graphical Abstract + 至少 1 张示意图。

---

## 5 & 6. 科研配图类

### 5. SciPilot Figure

专门面向科研论文的作图 Skill 集合，可生成符合期刊要求的 SVG 图表。

```
# GitHub 社区搜索 "scipilot-figure"
# 或通过社群获取安装地址
```

### 6. K-Dense Scientific Skills

包含 `scientific-schematics` skill，能生成流程图/示意图/Graphical Abstract。

```bash
claude plugin install scientific-skills@claude-scientific-skills
```

配合使用：
```bash
python scripts/generate_schematic.py "Graphical abstract for: [your title]" -o figures/
```

---

## 7. thesis-writer（中文论文）⭐⭐⭐⭐

**用途**：本科/研究生论文，GB/T 7714-2015 中文规范，支持工科/心理/教育/管理多学科

**GitHub**: `yanlin-cheng/skill-thesis-writer`

**安装**：
```bash
git clone https://github.com/yanlin-cheng/skill-thesis-writer.git

# Claude Code 项目级
mkdir -p .claude/skills
cp -r skill-thesis-writer .claude/skills/

# Codex
mkdir -p .codex/skills
cp -r skill-thesis-writer .codex/skills/
```

**兼容编辑器**：Cline, CodeBuddy, Cursor, Windsurf, Aider

**触发场景**：
- "帮我写一篇关于深度学习的论文开题报告"
- "把这些文献按 GB/T 7714 格式化"
- "检查这篇论文有没有逻辑问题"

---

## 8-12. 专项工具

### 8. Cite Verify（引文核验）

**用途**：DOI 验证、文献真实性检查、防止 AI 编造文献。

**原理**：对每条引用调 Semantic Scholar / Crossref API 验证真实性。

### 9. LaTeX Writer（智能排版）

**用途**：自动生成 LaTeX、表格排版、公式生成、格式适配。

适合：不熟悉 LaTeX 但需要投稿 LaTeX-only 期刊的研究者。

### 10. Stats Sanity（统计分析）

**用途**：显著性检验、数据合理性检查、实验设计评估、结果可信度分析。

**检查项**：p-hacking、多重比较校正、样本量、效应量、置信区间。

### 11. Paper RAG（文献知识库）

**用途**：基于 RAG 的多论文联合问答、文献知识管理、长期课题积累。

### 12. PaperSpine（论文拆解）

**用途**：论文结构拆解——把一篇论文拆成"脊椎"（核心论点链）。

---

## 安装故障排查

| 问题 | 解决 |
|------|------|
| "Skill not found" | 确认复制的是完整文件夹，不是只复制 SKILL.md |
| "Permission denied" | `chmod +x` 相关脚本 |
| "Plugin install failed" | 检查网络，重试一次 |
| "Dependency missing" | 查看 SKILL.md 开头的 requirements 段落 |
| 中文路径乱码 | 修改终端编码为 UTF-8 |

---

## 组合推荐

### 新手组合（最简）
```
Nature Skills + Scientific Writing
→ 覆盖润色 + 写作 + 图表
```

### 进阶组合（完整）
```
ARS (流程) + Nature Skills (图表) + Nature Paper Skills (投稿)
→ 从选题到投稿全覆盖
```

### 中文论文组合
```
thesis-writer + Nature Skills (图表) + LaTeX Writer
→ GB/T 7714 + 图表 + 排版
```

### 超大型项目组合
```
ARS (管道) + Nature Paper Skills (投稿) + Paper RAG (知识库) + Cite Verify (验证)
→ 带学术诚信闸门 + 知识积累 + 防幻觉
```
