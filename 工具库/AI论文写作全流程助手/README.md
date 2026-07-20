# AI 论文写作全流程助手

> 📝 让 AI 帮你从选题到投稿，每一步都有专业加持
> 
> 来源：飞书文档《AI辅助科研工具大全》精华提炼 | 黄永生 整理
> 开源：MIT License

---

## 一句话简介

这是一个 **Python + Markdown** 的论文写作全流程 AI 工具包。它不替代你写论文，而是告诉你在每个阶段：
- 📋 **该用什么 AI 工具**（安装命令 + GitHub 仓库）
- 📝 **该给 AI 下什么 Prompt**（模板直接复制）
- ⚠️ **该避免哪些坑**（每阶段 3 个实战避坑）

## 快速开始

```bash
# 交互式菜单（推荐新手）
python paper_ai_assistant.py

# 直接生成文献综述 Prompt
python paper_ai_assistant.py --stage lit-review

# 导出全流程 Markdown 指南
python paper_ai_assistant.py --export
```

## 覆盖的 8 个论文阶段

| # | 阶段 | AI 能帮你做什么 |
|---|------|----------------|
| 🔍 | 选题与开题 | Research gap 搜索、可行性评估、IMRaD 结构建议 |
| 📚 | 文献综述 | 10+ 文章自动摘要、对比表格、Gap 分析 |
| ⚙️ | 方法论设计 | 实验设计、伪代码、统计陷阱检查 |
| 🧪 | 实验与数据分析 | Python 可视化代码、统计显著性检验 |
| ✍️ | 论文撰写 | Nature 级别语言润色、Claim-Evidence 结构 |
| 📊 | 图表与可视化 | SVG 图表（Nature 投稿格式）、Figure Caption |
| ✨ | 润色与自查 | 语法/逻辑/术语/引用四维检查 |
| 📤 | 投稿与返修 | Cover Letter、逐条审稿回复策略 |

## 推荐的 12 个开源 AI Skills

| 工具 | 用途 | GitHub |
|------|------|--------|
| Nature Skills | Nature 论文全流程 | `Yuan1z0825/nature-skills` |
| ARS | 学术研究管道（苏格拉底式） | `Imbad0202/academic-research-skills` |
| SciPilot Figure | 科研作图集合 | 社区维护 |
| CCF Figure | CCF 级别科研配图 | 社区维护 |
| Paper RAG | 多论文联合问答 | 社区维护 |
| Cite Verify | 引文核验防幻觉 | 社区维护 |
| LaTeX Writer | 智能排版 | 社区维护 |
| Stats Sanity | 统计分析检查 | 社区维护 |
| Nature Paper Skills | Journal-first 投稿全链路 | `Boom5426/nature-paper-skills` |
| Scientific Writing | IMRaD + 引文格式 | `K-Dense-AI/claude-scientific-skills` |
| thesis-writer | 中文论文 GB/T 7714 | `yanlin-cheng/skill-thesis-writer` |
| K-Dense Scientific Skills | 科学图表 + Graphical Abstract | `K-Dense-AI/claude-scientific-skills` |

## 配套文档

| 文件 | 适合谁 |
|------|--------|
| `小白教程_从零开始用AI写论文.md` | 第一次用 AI 写论文的小白 |
| `论文写作Prompt模板库.md` | 想直接拿 Prompt 就用的 |
| `Skills工具安装速查手册.md` | 想装 Skills 但不知道怎么下手的 |
| `学术诚信与避坑指南.md` | 担心 AI 写作有风险的 |

## ⚠️ 重要提示

1. **AI 只是工具，不是作者**：所有内容需要你审阅、修改、验证
2. **引文必须手动验证**：AI 会编造不存在的论文（幻觉），每条引用用 DOI 查
3. **保留你的学术声音**：过度 AI 润色会让论文"AI味儿"太重
4. **投稿前用 AI 自查，不是替代审稿**：Submission Audit 是帮你找问题的，不是判决

## 适用场景

- ✅ 第一次写英文 SCI 论文的新手
- ✅ 想用 Claude Code / Codex 提升效率的科研党
- ✅ 需要结构化论文工作流的课题组
- ❌ 想"全自动"让 AI 代写的（学术不端）

---

## 📂 文件结构

```
AI论文写作全流程助手/
├── paper_ai_assistant.py          ← Python CLI 工具
├── README.md                       ← 本文件
├── 小白教程_从零开始用AI写论文.md
├── 论文写作Prompt模板库.md
├── Skills工具安装速查手册.md
└── 学术诚信与避坑指南.md
```

---

> 🔗 配套工具：`calcplot3d-url-gen`（论文 3D 数据可视化）
> 📖 参考来源：飞书《AI辅助科研工具大全》(黄永生) + ARS/Nature Skills/Codex 社区
