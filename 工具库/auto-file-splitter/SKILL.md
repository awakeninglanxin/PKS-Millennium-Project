---
name: "auto-file-splitter"
description: "一键检查并自动拆分目录下的Python/JavaScript文件。当检测到超过19KB的py/js文件时，自动调用python-file-splitter或js-file-splitter进行拆分，模块归档到XXXX_module格式的文件夹中。触发词：一键拆分、检查文件大小、批量拆分、自动拆分所有py文件、自动拆分所有js文件、文件体积检查、批量处理拆分。
---

# Auto File Splitter - 一键检查与自动拆分

## 概述

一键扫描指定目录下所有 Python/JavaScript 文件，检测超过 19KB 的文件，自动调用对应拆分器进行拆分，模块归档到 `原文件名_module/` 格式的文件夹中。

## 核心功能

1. **一键扫描** - 自动扫描目录下所有 py/js/ts/vue 文件
2. **大小检测** - 列出所有文件大小，标记超限文件
3. **自动拆分** - 超过19KB的文件自动拆分
4. **模块归档** - 拆分结果保存到 `XXXX_module/` 文件夹
5. **备份原文件** - 拆分前自动备份原始文件

## 使用流程

### 1. 执行一键检查

```bash
node ~/.workbuddy/skills/auto-file-splitter/scripts/scan_and_split.js [目录路径]
```

**示例**：
```bash
# 检查当前目录
node scan_and_split.js

# 检查指定目录
node scan_and_split.js ./src
node scan_and_split.js ./utils
node scan_and_split.js D:\project\components
```

### 2. 查看扫描结果

脚本会自动：
1. 扫描所有 py/js/ts/vue 文件
2. 显示每个文件的大小
3. 标记超过 19KB 的文件
4. 自动执行拆分

### 3. 拆分结果

```
原目录/
├── large_script.py              ← 原文件（已备份）
├── large_script.py.backup       ← 备份
├── large_script_module/         ← 拆分模块目录
│   ├── __init__.py
│   ├── function-a.py
│   ├── function-b.py
│   └── class-example.py
├── another_file.js
└── another_file_module/
    ├── index.js
    ├── helper-utils.js
    └── component-a.js
```

## 脚本位置

```
~/.workbuddy/skills/auto-file-splitter/scripts/scan_and_split.js
```

## 输出示例

```
============================================================
🔍 一键文件拆分检查器
============================================================
📁 扫描目录: D:\project\src
📏 大小限制: 19KB
============================================================

📂 扫描文件中...
   发现 15 个目标文件

📊 检查文件大小...

   ─────────────────────────────────────────────────────────
   文件名                                    大小         状态
   ─────────────────────────────────────────────────────────
   app.js                                    25.3KB      ⚠️ 超限
   utils.js                                  8.2KB       ✅ 正常
   helpers.py                                32.1KB      ⚠️ 超限
   components.vue                             18.5KB      ✅ 正常
   ─────────────────────────────────────────────────────────
   超限文件: 2 个

🔄 开始自动拆分...

📦 处理: app.js
   📋 已备份: app.js → app.js.backup
   ✅ 拆分完成 → app_module/

📦 处理: helpers.py
   📋 已备份: helpers.py → helpers.py.backup
   ✅ 拆分完成 → helpers_module/

============================================================
📊 一键拆分报告
============================================================
📁 扫描目录: D:\project\src
📂 扫描文件: 15 个
⚠️  超限文件: 2 个
✅ 已拆分: 2 个
❌ 失败: 0 个

📦 拆分结果:
   • app.js → app_module/
   • helpers.py → helpers_module/

🎉 检查完成！
============================================================
```

## 执行流程

```
1. 扫描目录 → 收集所有 py/js/ts/vue 文件
2. 检查大小 → 标记超过 19KB 的文件
3. 备份原文件 → xxx.backup
4. 调用拆分器 → python-file-splitter 或 js-file-splitter
5. 模块归档 → 保存到 XXXX_module/ 目录
6. 生成报告 → 显示拆分结果
```

## 排除目录

扫描时自动排除：
- `node_modules/`
- `__pycache__/`
- `.git/`
- 已有 `_module` 后缀的目录

## 依赖

此 Skill 依赖以下 Skill：
- `python-file-splitter` - 拆分 Python 文件
- `js-file-splitter` - 拆分 JavaScript/TypeScript 文件

## CODE_INDEX.md 自动索引机制

每次批量拆分完成后，脚本自动在**被扫描目录**生成/更新 `CODE_INDEX.md`。

### 索引文件的作用

AI 每次收到用户指令时，**先读 `CODE_INDEX.md`**，可快速定位：
- 整个项目的文件结构一览
- UI 入口（HTML）→ 按钮 → 处理函数 的完整链路
- 所有源文件的函数/类列表
- 文件依赖关系图
- 无需逐一读取所有源文件，节约 token

### 核心文件 vs 知识字典文件

索引**只收录核心源文件**，自动跳过：
- 文件名含 `knowledge_base`、`_data`、`_dict`、`_config`、`constants` 的纯数据文件
- `__pycache__`、`node_modules`、`.git` 等目录

手动触发索引更新（适合修改了核心文件但未做拆分的情况）：
```bash
python ~/.workbuddy/skills/python-file-splitter/scripts/generate_index.py <项目目录>
```

## 注意事项

1. **备份机制** - 拆分前自动备份原文件，扩展名为 `.backup`
2. **模块命名** - 拆分后的模块统一保存到 `原文件名_module/` 目录
3. **递归扫描** - 默认递归扫描所有子目录
4. **跨平台** - 支持 Windows/macOS/Linux
5. **索引依赖** - 需要 Python 3.9+ 运行 `generate_index.py`
