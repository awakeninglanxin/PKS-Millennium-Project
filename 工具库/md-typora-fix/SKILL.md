# md-typora-fix — Typora MD 公式兼容性自动修复

## 功能

扫描 MD 文件中 `$$...$$` 和 `$...$` 公式块内的中文文本和英文标签，自动包裹 `\text{}` 使其在 Typora 中正常渲染。

## 触发条件

- 用户说 "Typora 公式乱码" / "公式不兼容 Typora" / "修复 MD 公式"
- 生成了新的 MD 文件含数学公式
- 用户发现公式中的中文或英文标签渲染异常

## 调用方式

```bash
# 修复整个项目目录
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/md-typora-fix/md_typora_fix.py "目标目录"

# 预览模式
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/md-typora-fix/md_typora_fix.py "目标目录" --dry-run

# 修复单个文件
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/md-typora-fix/md_typora_fix.py "文件.md"
```

## 修复规则

| 内容 | 位置 | 操作 |
|------|------|------|
| 中文/全角字符 | `$$...$$` 或 `$...$` 内 | 包裹 `\text{中文}` |
| 英文单词 (≥3字母) | 下标 `_{word}` | 包裹 `_{\text{word}}` |
| 普通文字 | 公式外 | 不动 |

## 示例

```
修复前:
  $$密度(n) \propto e^n$$
  $$E_{tip} \propto \frac{V}{r_{tip}}$$

修复后:
  $$\text{密度}(n) \propto e^n$$
  $$E_{\text{tip}} \propto \frac{V}{r_{\text{tip}}}$$
```

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
