#!/usr/bin/env python3
"""
AI论文写作全流程助手 — 从选题到投稿的完整AI工具链
==============================================
基于飞书文档《AI辅助科研工具大全》的精华提炼与实战整合。
支持 8 个论文阶段 × 4 种 AI 助手 (Claude Code / Codex / ChatGPT / Custom)
每个阶段自动生成：
  - 适配当前写作阶段的 AI Prompt 模板
  - 推荐 Skills 工具 & 安装命令
  - 常见陷阱提醒

用法:
    python paper_ai_assistant.py                     # 交互式菜单
    python paper_ai_assistant.py --stage lit-review   # 直接生成文献综述 Prompt
    python paper_ai_assistant.py --stage abstract     # 生成摘要 Prompt
    python paper_ai_assistant.py --stage all          # 生成全部8阶段Prompt合辑
    python paper_ai_assistant.py --export             # 导出全流程 Markdown 指南
"""

import argparse
import os
import sys
from datetime import datetime

# ============================================================
# 阶段定义 — 每个阶段包含 Prompt模板 + 推荐工具 + 避坑指南
# ============================================================

STAGES = {
    "topic": {
        "name": "选题与开题",
        "emoji": "🔍",
        "skills": [
            ("ARS (论文流程)", "Imbad0202/academic-research-skills", "/ars-plan"),
            ("Scientific Writing", "K-Dense-AI/claude-scientific-skills", "/scientific-writing"),
        ],
        "prompt_template": """我现在正在研究 [{研究方向}] 方向，准备选定一个论文题目。
请帮我：
1. 列出该方向 3-5 个前沿研究缺口（research gap）
2. 评估每个缺口的创新性和可行性（1-10打分）
3. 对最有潜力的题目，用一句话给出核心研究问题（research question）
4. 给出选题的初步 IMRaD 结构建议

我的背景信息：
- 研究领域：{研究领域}
- 已掌握方法：{方法}
- 目标期刊类型：{期刊类型}""",
        "traps": [
            "选题太大：AI一句话写不完的不是好题目",
            "只追热点没有自己数据：LLM幻觉 + 无数据 = 论文被毙",
            "先搜文献确认 gap 是否真实存在，再确定题目",
        ],
    },
    "lit-review": {
        "name": "文献综述",
        "emoji": "📚",
        "skills": [
            ("ARS 文献综述", "Imbad0202/academic-research-skills", "/ars-lit-review"),
            ("Paper RAG", "论文知识库 RAG 工具", "/paper-rag"),
            ("PaperSpine", "论文拆解工具", "论文结构提取"),
        ],
        "prompt_template": """请帮我系统性地综述 [{研究主题}] 的相关文献。

要求：
1. 按时间线/方法线/结论线三维度组织
2. 每篇文献提取：方法、数据集、核心指标、局限性
3. 生成对比表格（至少 10 篇核心文献）
4. 用一段话总结现有方法的共同局限

文献来源偏好：Semantic Scholar / arXiv / PubMed
输出格式：Markdown 表格 + 结构化段落""",
        "traps": [
            "AI编造文献：每篇引用必须手动验证 DOI！",
            "综述 ≠ 堆砌：需要你自己的分类逻辑线",
            "先读 10 篇核心，再做综述，不要倒过来",
        ],
    },
    "method": {
        "name": "方法论设计",
        "emoji": "⚙️",
        "skills": [
            ("Stats Sanity", "统计分析检验工具", "统计合理性检查"),
            ("Scientific Writing", "K-Dense-AI/claude-scientific-skills", "方法章节撰写"),
        ],
        "prompt_template": """我正在设计论文的实验方法，请帮我完善方法论部分。

研究问题：{研究问题}
数据集：{数据集描述}
baseline 方法：{baseline方法}

请：
1. 给出实验设计（变量、对照组、评估指标）
2. 检查是否有统计陷阱（p-hacking、样本量不足、多重比较）
3. 用伪代码描述核心算法流程
4. 推荐 3 个合适的评估指标并解释为什么选它们""",
        "traps": [
            "实验不可复现：所有超参数/随机种子必须记录",
            "指标单一：至少3个互补指标（如Accuracy+F1+AUC）",
            "没有ablation：去掉每个组件看贡献",
        ],
    },
    "experiment": {
        "name": "实验与数据分析",
        "emoji": "🧪",
        "skills": [
            ("SciPilot Figure", "科研绘图", "scipilot-figure-skill"),
            ("CCF Figure", "CCF级别科研配图", "CCF Figure"),
            ("Stats Sanity", "统计分析", "显著性检验"),
        ],
        "prompt_template": """请帮我分析以下实验数据并生成可视化方案。

数据描述：{数据描述}
对比方法：{方法列表}
主要发现：{发现}

请：
1. 推荐 4 种最适合的数据可视化类型（含使用理由）
2. 给出一张最关键的对比图表的 Python (matplotlib/seaborn) 代码
3. 进行统计显著性检验，告诉我 p 值
4. 列出一个结果表格的 LaTeX 代码""",
        "traps": [
            "图表没有 error bar / 置信区间",
            "只用柱状图一种类型",
            "颜色对色盲不友好（避免红绿搭配）",
        ],
    },
    "writing": {
        "name": "论文撰写",
        "emoji": "✍️",
        "skills": [
            ("Nature Skills 全流程", "Yuan1z0825/nature-skills", "nature-figure + nature-polish"),
            ("ARS 撰写阶段", "Imbad0202/academic-research-skills", "/ars-write"),
            ("LaTeX Writer", "LaTeX 排版工具", "LaTeX 公式/表格"),
        ],
        "prompt_template": """请帮我撰写论文的 [{章节名称}] 部分。

论文章节：{章节名称}
核心论点：{核心论点}
关键证据：{关键证据}

要求：
1. 符合 Nature/Science 级别学术写作规范
2. 每个段落包含：Claim → Evidence → Link
3. 不要用 bullet points，用流畅的段落叙述
4. 控制被动语态占比 < 40%
5. 如果这是 Results，确保每段只讲一个主要发现""",
        "traps": [
            "Abstract 比正文证据强：先写正文，最后写摘要",
            "Introduction 太长：控制在 1.5 页内",
            "Discussion 只是重复 Results：Discussion 要解释'为什么'",
        ],
    },
    "figures": {
        "name": "图表与可视化",
        "emoji": "📊",
        "skills": [
            ("Nature Figure (SVG)", "Yuan1z0825/nature-skills", "nature-figure"),
            ("SciPilot Figure", "科研绘图集合", "scipilot-figure-skill"),
        ],
        "prompt_template": """我需要为论文生成一张关键图表。

图表类型：{图表类型}
数据描述：{数据描述}
目标期刊风格：Nature / Science / IEEE

请：
1. 描述整张图的设计方案（panel布局 + 颜色方案）
2. 给出 figure caption 的初稿（遵循目标期刊格式）
3. 用 Python + matplotlib 写出完整绘制代码
4. 如果要导出 SVG（适合 Nature 投稿），给出提示词给 AI 绘图工具""",
        "traps": [
            "一图多claim：每张主图只承载一个核心结论",
            "图注只是解释坐标轴：图注是结果叙述的第二层",
            "没标注统计信息：必须有 error bar / p值 / n值",
        ],
    },
    "polish": {
        "name": "润色与自查",
        "emoji": "✨",
        "skills": [
            ("Nature Polish", "Yuan1z0825/nature-skills", "nature-polish"),
            ("Cite Verify", "引文验证工具", "DOI核验"),
            ("Submission Audit", "投稿前预检", "submission-audit"),
        ],
        "prompt_template": """请帮我润色检查以下论文段落。

[粘贴你的文字]

检查清单：
1. 语法与拼写错误
2. 学术表达规范（避免口语化）
3. 逻辑流畅性（段落间的过渡）
4. 术语一致性（同一概念是否用同一术语）
5. 引用是否完整（每个 claim 是否有文献支撑）

请列出所有问题 + 具体修改建议，不要直接重写。""",
        "traps": [
            "过度润色 → AI味儿太重：保留你的学术声音",
            "只检查语法不检查逻辑：AI不懂你的领域知识",
            "引用幻觉：每条引文用 DOI 验证",
        ],
    },
    "submit": {
        "name": "投稿与返修",
        "emoji": "📤",
        "skills": [
            ("Submission Audit", "Boom5426/nature-paper-skills", "submission-audit"),
            ("Rebuttal Response", "Boom5426/nature-paper-skills", "rebuttal-response"),
            ("Data Availability", "数据可用性声明", "data-availability"),
        ],
        "prompt_template": """请帮我处理论文投稿/返修事宜。

场景：{投稿/返修}
期刊：{期刊名称}
审稿意见或要求：{详情}

请：
1. 如果是投稿：检查 cover letter、highlights、作者贡献声明
2. 如果是返修：按审稿人意见逐条回复策略
   - 对每条审稿意见：先礼貌回应，再说明如何修改，最后指出修改位置
3. 检查 Data Availability Statement
4. 核对所有引用格式是否匹配目标期刊""",
        "traps": [
            "忽略审稿人的语气信号：每条意见都必须认真回应",
            "返修信写太长：审稿人不看小说",
            "数据可用性声明空洞：必须有具体仓库/accession号",
        ],
    },
}

# ============================================================
# Skills 工具库
# ============================================================
SKILLS_DB = [
    {"name": "Nature Skills", "desc": "Nature 风格论文全流程（润色/图表/引文/审稿回复）",
     "repo": "Yuan1z0825/nature-skills", "install": "claude plugin install nature-skills"},
    {"name": "ARS (论文管道)", "desc": "从研究→撰写→评审→修改→定稿的全流程",
     "repo": "Imbad0202/academic-research-skills", "install": "/plugin marketplace add Imbad0202/academic-research-skills"},
    {"name": "SciPilot Figure", "desc": "面向科研论文的作图 Skill 集合",
     "repo": "scipilot-figure-skill", "install": "按社区文档安装"},
    {"name": "CCF Figure", "desc": "CCF 级别科研配图生成",
     "repo": "待确认", "install": "待补充"},
    {"name": "Paper RAG", "desc": "多论文联合问答 + 文献知识管理",
     "repo": "待确认", "install": "待补充"},
    {"name": "Cite Verify", "desc": "DOI 验证、文献真实性检查、防 AI 编造",
     "repo": "待确认", "install": "待补充"},
    {"name": "LaTeX Writer", "desc": "自动生成 LaTeX、表格排版、公式生成",
     "repo": "待确认", "install": "待补充"},
    {"name": "Stats Sanity", "desc": "显著性检验、数据合理性检查",
     "repo": "待确认", "install": "待补充"},
    {"name": "PaperSpine", "desc": "论文结构拆解与分析",
     "repo": "待确认", "install": "待补充"},
    {"name": "Nature Paper Skills", "desc": "Nature 投稿全链路（Journal-first, claim-driven）",
     "repo": "Boom5426/nature-paper-skills", "install": "git clone + 复制 skill 目录"},
    {"name": "Scientific Writing", "desc": "IMRAD 结构 + APA/AMA/Vancouver 引文格式",
     "repo": "K-Dense-AI/claude-scientific-skills", "install": "claude plugin install scientific-skills"},
    {"name": "thesis-writer", "desc": "本科/研究生论文 GB/T 7714 中文规范",
     "repo": "yanlin-cheng/skill-thesis-writer", "install": "git clone + 复制到 .claude/skills/"},
]


# ============================================================
# Claude Code / Codex 安装速查
# ============================================================
INSTALL_GUIDE = """
## Claude Code 安装

```bash
# 方式1: npm 全局安装
npm install -g @anthropic-ai/claude-code
claude  # 启动

# 方式2: VS Code 扩展
# 在 VS Code 扩展市场搜索 "Claude Code" 并安装

# 安装 Plugin (推荐方式装 Skills):
claude plugin marketplace add Yuan1z0825/nature-skills
claude plugin install nature-skills

# 手动安装 Skills:
mkdir -p ~/.claude/skills/
cp -R nature-skills/skills/nature-* ~/.claude/skills/
```

## OpenAI Codex 安装

```bash
# 方式1: npm 全局安装
npm install -g @openai/codex
codex  # 启动

# 方式2: 官方桌面 App
# 下载: https://openai.com/codex/

# 方式3: VS Code 扩展

# 安装 Skills (Plugin 方式):
/plugin marketplace add [repo-url]
/plugin install [skill-name]
```

## 第一次使用的 4 个必须设置

1. **建项目文件夹**: `~/codex-projects/paper-xxx/`（不要放桌面/下载）
2. **设置 AGENTS.md**: 告诉 AI 用中文回答、不碰 .env、先问不清楚的
3. **权限选"默认"**: 修改文件需要你手动确认（新手别开 Full Access）
4. **组合键发送**: 把 Enter 发送改成 Ctrl+Enter 发送（防止半句话就发出去）
"""


# ============================================================
# 交互式菜单
# ============================================================
def interactive_menu():
    """显示交互式菜单"""
    print("\n" + "=" * 60)
    print("  📝 AI 论文写作全流程助手 v1.0")
    print("  从选题 → 投稿，每个阶段都有 AI 加持")
    print("=" * 60)
    print("\n请选择论文写作阶段：\n")

    for key, stage in STAGES.items():
        print(f"  {stage['emoji']}  [{key:12s}]  {stage['name']}")

    print(f"\n  📦  [{'skills':12s}]  查看全部推荐 Skills 工具")
    print(f"  📖  [{'guide':12s}]    Claude Code / Codex 安装速查")
    print(f"  📤  [{'all':12s}]      导出全流程 Markdown 指南")
    print(f"  🚪  [{'quit':12s}]     退出")
    print()

    choice = input(">>> ").strip().lower()

    if choice == "quit":
        print("\n祝论文顺利！🎓\n")
        sys.exit(0)
    elif choice == "skills":
        show_skills()
    elif choice == "guide":
        show_install_guide()
    elif choice == "all":
        export_all()
    elif choice in STAGES:
        show_stage(choice)
    else:
        print(f"\n⚠️  未知选项: {choice}，请重新选择。")
        interactive_menu()

    # 循环
    input("\n按 Enter 返回主菜单...")
    interactive_menu()


def show_stage(key):
    """展示单个阶段的完整信息"""
    stage = STAGES[key]
    print(f"\n{'=' * 60}")
    print(f"  {stage['emoji']} 阶段: {stage['name']}")
    print(f"{'=' * 60}")

    # 推荐工具
    print(f"\n🛠️  推荐 Skills 工具：")
    for i, (name, repo, cmd) in enumerate(stage["skills"]):
        print(f"  {i+1}. {name}")
        print(f"     仓库: {repo}")
        print(f"     命令: {cmd}")
        print()

    # Prompt 模板
    print(f"\n📋 Prompt 模板 (复制到对话中使用)：")
    print("-" * 50)
    print(stage["prompt_template"])
    print("-" * 50)

    # 避坑
    print(f"\n⚠️  常见陷阱：")
    for t in stage["traps"]:
        print(f"  ❌ {t}")


def show_skills():
    """展示所有推荐 tools"""
    print(f"\n{'=' * 60}")
    print("  📦 推荐的 AI 科研 Skills 工具库 (12个)")
    print(f"{'=' * 60}\n")
    for i, s in enumerate(SKILLS_DB):
        print(f"  {i+1:2d}. {s['name']}")
        print(f"      {s['desc']}")
        print(f"      GitHub: {s['repo']}")
        print(f"      安装: {s['install']}")
        print()


def show_install_guide():
    """展示安装速查"""
    print(f"\n{'=' * 60}")
    print("  📖 Claude Code / Codex 安装速查")
    print(f"{'=' * 60}")
    print(INSTALL_GUIDE)


def export_all():
    """导出全流程 Markdown 指南"""
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"AI论文写作全流程指南_{datetime.now().strftime('%Y%m%d')}.md")

    lines = []
    lines.append("# AI 论文写作全流程指南\n")
    lines.append(f"> 生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("> 来源: 飞书文档《AI辅助科研工具大全》+ 实战整合\n")
    lines.append("---\n")

    for key, stage in STAGES.items():
        lines.append(f"## {stage['emoji']} 阶段: {stage['name']}\n")
        lines.append("### 推荐工具\n")
        for name, repo, cmd in stage["skills"]:
            lines.append(f"- **{name}**: `{repo}` → `{cmd}`\n")
        lines.append("\n### Prompt 模板\n")
        lines.append("```\n" + stage["prompt_template"] + "\n```\n")
        lines.append("### ⚠️ 避坑\n")
        for t in stage["traps"]:
            lines.append(f"- ❌ {t}\n")
        lines.append("\n---\n")

    # Skills 库
    lines.append("## 📦 推荐 Skills 工具库\n")
    for s in SKILLS_DB:
        lines.append(f"- **{s['name']}**: {s['desc']} → `{s['repo']}`\n")

    # 安装指南
    lines.append("\n## 📖 安装指南\n")
    lines.append(INSTALL_GUIDE)

    with open(out_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n✅ 已导出: {out_file}")


# ============================================================
# 命令行入口
# ============================================================
def main():
    ap = argparse.ArgumentParser(
        description="AI论文写作全流程助手 — 从选题到投稿的8阶段AI工具链",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                       交互式菜单
  %(prog)s --stage lit-review    生成文献综述 Prompt
  %(prog)s --stage abstract      生成摘要 Prompt
  %(prog)s --stage all           导出全部8阶段指南
  %(prog)s --skills              列出推荐工具
  %(prog)s --guide               Claude/Codex 安装速查
        """,
    )
    ap.add_argument("--stage", "-s", default=None,
                    choices=list(STAGES.keys()) + ["all", "skills", "guide"],
                    help="直接跳转到指定阶段")
    ap.add_argument("--export", "-e", action="store_true",
                    help="导出全流程 Markdown 文件")

    args = ap.parse_args()

    if args.export:
        export_all()
    elif args.stage == "all":
        export_all()
    elif args.stage == "skills":
        show_skills()
    elif args.stage == "guide":
        show_install_guide()
    elif args.stage in STAGES:
        show_stage(args.stage)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
