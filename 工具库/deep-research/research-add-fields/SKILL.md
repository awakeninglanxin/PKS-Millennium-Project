---
user-invocable: true
description: 向现有调研outline补充字段定义。
allowed-tools: Bash, Read, Write, Glob, WebSearch, Task, AskUserQuestion
---

# Research Add Fields - 补充调研字段

## 触发方式
`/research-add-fields`

## 执行流程

### Step 1: 自动定位Fields文件
在当前工作目录查找 `*/fields.yaml` 文件，自动读取现有fields定义。

### Step 2: 获取补充来源
询问用户选择：
- **A. 用户直接输入**：用户提供字段名称和描述
- **B. Web Search搜索**：启动web-search-agent搜索该领域常用字段

### Step 3: 展示并确认
- 展示建议的新字段列表
- 用户确认哪些字段需要添加
- 用户指定字段分类和detail_level

### Step 4: 保存更新
将确认的字段追加到fields.yaml，保存文件。

## 输出
更新后的 `{topic}/fields.yaml` 文件（原地修改，需用户确认）

---

> ⚠️ **重要声明 / Important Disclaimer**
> 
> 本文档由 AI 辅助生成，部分结论可能存在 AI 幻觉导致的论证不严谨之处。
> 文中提出的数学、物理及相关跨学科观点，需要经过专业数学家、物理学家
> 及相关领域专家共同验证与检验。
> 如有疏漏、错误或不同见解，敬请指正，不胜感激。
> 
> **This document was AI-assisted. Some conclusions may contain inaccuracies
> due to AI hallucination. All mathematical, physical, and interdisciplinary
> claims require verification by professional mathematicians, physicists,
> and subject-matter experts. Corrections and feedback are warmly welcomed.**
