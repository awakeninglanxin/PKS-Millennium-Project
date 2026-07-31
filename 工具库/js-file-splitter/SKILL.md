---
name: "js-file-splitter"
description: "智能JavaScript/TypeScript文件拆分工具，用于将大型JS/TS文件拆分成多个不超过19KB的子文件。触发词：拆分JS文件、文件太大JS、分成多个js文件、超过19KB JS、代码拆分JS、模块化拆分、js文件分割。This skill should be used when: 用户要求将大型JavaScript/TypeScript文件拆分成多个小文件、React组件拆分、Vue文件拆分、每个文件不超过19KB限制、代码模块化重构。
---

# JavaScript/TypeScript File Splitter

## 概述

将超过19KB的JavaScript/TypeScript文件智能拆分成多个不超过19KB的子文件，支持React组件、Vue单文件组件、ES6模块和CommonJS。

## 核心功能

1. **智能拆分** - 自动识别函数、类、组件
2. **组件识别** - 自动识别React/Vue组件
3. **模块生成** - 自动生成index.js入口文件
4. **大小验证** - 确保所有文件≤19KB
5. **可选Babel** - 支持Babel AST解析（可选）

## 使用流程

### 1. 分析文件

读取目标JS/TS文件，分析其结构：
- 函数声明 (function, arrow function)
- 类声明 (class)
- 组件识别 (React/Vue)
- Import/Export 语句

### 2. 执行拆分

```bash
node ~/.workbuddy/skills/js-file-splitter/scripts/smart_split.js <输入文件> [输出目录]
```

**示例**：
```bash
# 基本用法
node smart_split.js app.js modules

# React组件
node smart_split.js src/App.jsx components --framework react

# 指定输出目录
node smart_split.js utils/helpers.ts lib
```

### 3. CLI 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--maxSize` | 最大文件大小(KB) | 19 |
| `--framework` | 框架类型 | vanilla |
| `--moduleType` | 模块类型 | esm |

## 脚本位置

```
~/.workbuddy/skills/js-file-splitter/scripts/smart_split.js
```

## 拆分策略

### 按组件拆分

识别React/Vue组件，生成独立文件：
```
components/
├── my-component.js
├── user-profile.js
└── dashboard.js
```

### 按类拆分

每个类生成独立文件：
```
models/
├── user-model.js
├── order-model.js
└── product-model.js
```

### 按函数拆分

工具函数按需拆分：
```
utils/
├── format-date.js
├── validate-email.js
└── calculate-price.js
```

## 输出结构

```
项目/
├── modules/              # 拆分后的模块目录
│   ├── index.js          # 入口文件（聚合导出）
│   ├── my-component.js
│   ├── user-model.js
│   └── format-date.js
└── original-file.js      # 原始文件（保留）
```

## 示例输出

```bash
$ node smart_split.js App.jsx components

============================================================
🔄 JavaScript/TypeScript 文件拆分器
============================================================
📄 输入文件: App.jsx
📁 输出目录: components
📏 最大文件大小: 19456 字节 (19KB)
============================================================

📊 源文件大小: 25000 字节 (24.4KB)

📋 代码结构分析:
  • Class: UserProfile (8.2KB) [组件]
  • Class: Dashboard (12.1KB) [组件]
  • Function: helper (0.5KB)
  • Imports: 5 个
  • Exports: 2 个

🔧 开始拆分...
  ✓ 生成: user-profile.js
  ✓ 生成: dashboard.js
  ✓ 生成: helper.js
  ✓ 生成主文件: index.js

============================================================
📊 拆分报告
============================================================
📄 源文件: App.jsx (24.4KB)
📁 生成模块: 4 个
📏 所有文件 ≤19KB: ✅ 是
============================================================
🎉 拆分完成!
============================================================
```

## 组件识别

### React 组件特征
- 返回JSX (`return (<...>)`)
- 使用 `useState`, `useEffect`, `useCallback`, `useMemo`
- `React.createElement()` 调用

### Vue 组件特征
- `defineComponent()` 调用
- `setup()` 函数
- `ref()`, `reactive()`, `computed()` 组合式API

## 注意事项

1. **Babel依赖（可选）** - 安装 `@babel/parser` 等包可获得更精确的AST解析
2. **依赖分析** - 当前版本简化了依赖分析，大型项目建议手动检查导入
3. **TypeScript** - 需要在支持TS的环境中运行，或先转译为JS

## 备份机制（v1.1 新增）

**拆分前自动备份**，确保原始文件永不丢失：

```
拆分前:  gdv_chart.js
备份为: gdv_chart.2026-04-24T10-30-00.backup.js
拆分后: gdv_chart.js (入口文件) + modules/ (子模块)
```

备份文件按时间戳命名，自动保留最新3个，自动清理更旧的备份。

## 压缩单行JS支持（v1.1 新增）

支持分析压缩/混淆的单行JS文件（如自动生成的图表绑定文件）：

- **自动检测**：行数少但字节大的文件自动识别为压缩JS
- **Prettier 格式化**：尝试用 prettier 格式化后分析（需 npx）
- **手动格式化备选**：prettier 不可用时自动降级
- **常量/函数分离**：全局变量、函数、可执行语句各自独立文件

### ⚠️ 图表绑定文件警告

自动生成的 Chart.js/Plotly/ECharts 绑定文件（如包含 `new Chart(...)` + 长数据数组），拆分后会破坏功能。脚本会**检测并警告**，但仍可强制执行。

```bash
# 强制拆分压缩JS（含图表绑定文件）
node smart_split.js chart.js --force
```

## CLI 选项（v1.1 完整）

| 选项 | 说明 |
|------|------|
| `--skipBackup` | 跳过备份（如已在 auto-file-splitter 层面备份） |
| `--force` | 强制拆分（包括压缩JS和图表绑定文件） |
| `--framework` | react / vue / vanilla |

## CODE_INDEX.md 自动索引机制

每次拆分完成后，脚本自动调用 `generate_index.py` 在**项目目录**生成/更新 `CODE_INDEX.md`。

### 索引文件的作用

AI 每次收到用户指令时，**先读 `CODE_INDEX.md`**，可快速定位：
- 哪个 JS 文件负责哪个功能模块
- 导出函数与其他文件的依赖关系
- UI 按钮/事件处理器的映射
- 无需逐一读取所有文件，节约 token

### 核心文件 vs 知识字典文件

**核心源文件**（进入索引）：含函数、类、路由、UI 逻辑的文件

**知识字典文件**（自动排除）：文件名含 `_data`、`_dict`、`constants`、`knowledge_base` 等关键词的纯数据文件

手动触发索引更新：
```bash
python ~/.workbuddy/skills/python-file-splitter/scripts/generate_index.py <项目目录>
```

## 踩坑经验

- Windows环境需要Node.js 14+支持UTF-8
- 大型依赖图需要手动重构导入语句
- Vue SFC建议使用 `@vue/compiler-sfc` 解析
