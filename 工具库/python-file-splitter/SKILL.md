---
name: "python-file-splitter"
description: "智能Python文件拆分工具，用于将超过19KB的Python文件拆分成多个不超过19KB的子文件。触发词：拆分Python文件、文件太大、分成多个py文件、超过19KB、代码拆分、模块化拆分、py文件分割、自动拆分脚本。This skill should be used when: 用户要求将大型Python文件拆分成多个小文件、每个文件不超过19KB限制、代码模块化重构、生成入口文件main.py。
---

# Python File Splitter - 智能Python文件拆分器

## 概述

将超过19KB的Python文件智能拆分成多个不超过19KB的子文件，同时保持代码的逻辑完整性和可运行性。

## 核心功能

1. **智能拆分**：按函数/类进行逻辑拆分
2. **二次拆分**：超大函数/类自动进一步拆分
3. **自动导入**：生成正确的import语句
4. **入口文件**：自动创建main.py入口文件
5. **大小验证**：确保所有文件≤19KB

## 使用流程

### 1. 分析文件

首先读取目标文件，分析其结构：

```
分析 /path/to/large_script.py 的代码结构，识别：
1. 所有函数及其大小
2. 所有类及其大小  
3. 哪些部分可能超过19KB限制
4. 给出拆分建议
```

### 2. 执行拆分

使用内置的 `smart_split.py` 脚本执行拆分：

```bash
python ~/.workbuddy/skills/python-file-splitter/scripts/smart_split.py <输入文件> [输出目录]
```

**示例**：
```bash
# 基本用法
python smart_split.py large_script.py

# 指定输出目录
python smart_split.py large_script.py modules
```

### 3. 验证结果

脚本会自动：
- 检查每个生成文件的大小
- 报告超过限制的文件
- 提供修复建议

## 脚本位置

```
~/.workbuddy/skills/python-file-splitter/scripts/smart_split.py
```

## 拆分策略

### 按函数拆分

当单个函数超过19KB时，按逻辑段落进一步拆分：

```python
# 原始大函数
def process_data(data):
    # 大量代码...

# 拆分成多个小函数
def process_data_part1(data):
    # 第一部分逻辑

def process_data_part2(data):
    # 第二部分逻辑
```

### 按类拆分

当单个类超过19KB时，按方法拆分为多个小类：

```python
# 原始大类
class DataProcessor:
    def method1(self): ...
    def method2(self): ...
    def method3(self): ...

# 拆分成多个小类
class DataProcessor_method1:
    def method1(self): ...
    # + 公共属性

class DataProcessor_method2:
    def method2(self): ...
    # + 公共属性
```

### 按模块聚合

多个小函数/类聚合到同一文件，确保总大小≤19KB：

```
module_000.py (函数A + 函数B + 类A)
module_001.py (函数C + 类B)
module_002.py (超大函数D_part1)
module_003.py (超大函数D_part2)
```

## 输出结构

```
目标文件/
├── modules/                  # 拆分后的模块目录
│   ├── __init__.py
│   ├── module_000.py
│   ├── module_001.py
│   └── ...
├── main.py                   # 主入口文件（聚合导入）
└── original_file.py          # 原始文件（保留备份）
```

## 使用示例

### 示例1：拆分单个大文件

```bash
python smart_split.py reports_generator.py
```

输出：
```
============================================================
🔄 智能Python文件拆分器
============================================================
📄 输入文件: reports_generator.py
📁 输出目录: modules
📏 最大文件大小: 19456 字节 (19KB)
============================================================

📊 源文件大小: 45000 字节 (43.9KB)

📋 代码结构分析:
  • ClassDef: ReportGenerator (32000字节 31.3KB) ⚠️ 超过限制
  • FunctionDef: generate_report (12000字节 11.7KB)
  • FunctionDef: helper_function (1500字节 1.5KB)

🔧 开始拆分...
  ⚠️ 类 'ReportGenerator' 过大，开始智能拆分...
    ✓ 拆分为 3 个文件

🔍 验证文件大小...
✓ 生成: module_000.py
✓ 生成: module_001.py
✓ 生成: module_002.py
✓ 生成: module_003.py

============================================================
📊 拆分报告
============================================================
📄 源文件: reports_generator.py (43.9KB)
📁 生成模块: 5 个
📏 所有文件 ≤19KB: ✅ 是
============================================================
🎉 拆分完成!
============================================================
```

### 示例2：指定输出目录

```bash
python smart_split.py my_large_app.py src_split
```

## 注意事项

1. **语法完整性**：拆分时自动保持Python语法完整性
2. **导入关系**：自动生成正确的import语句
3. **命名冲突**：如果存在命名冲突，在输出中提示用户
4. **特殊语法**：复杂动态代码可能需要手动调整

## CODE_INDEX.md 自动索引机制

每次拆分完成后，脚本自动调用 `generate_index.py` 在**项目目录**生成/更新 `CODE_INDEX.md`。

### 索引文件的作用

AI 每次收到用户指令时，**先读 `CODE_INDEX.md`**，可快速定位：
- 哪个源文件负责哪段逻辑
- UI 按钮/链接背后连接到哪个处理函数
- 文件之间的 import 依赖关系
- 无需读遍所有源文件，节约 token

### 核心文件 vs 知识字典文件

**核心源文件**（进入索引）：
- 含有业务逻辑、路由、UI 交互的 `.py` / `.js` 文件

**知识字典文件**（自动排除，不进索引）：
- 文件名含 `knowledge_base`、`_data`、`_dict`、`_config`、`constants` 等关键词
- 纯数据/纯文本，不含可执行逻辑

如需手动指定额外排除文件，可调用：
```bash
python generate_index.py <项目目录> --exclude knowledge_base.py,data_maps.py
```

### 何时手动触发索引更新

当你修改了核心源文件（不含字典文件）但未做拆分操作时，可手动更新索引：
```bash
python ~/.workbuddy/skills/python-file-splitter/scripts/generate_index.py <项目目录>
```

## 踩坑经验

- 使用 `ast.unparse()` 需要Python 3.9+，低版本需要回退到 `astor` 或 `astpretty`
- 拆分后的代码需要用户验证导入路径是否正确
- 如果原文件有 `if __name__ == "__main__"` 块，需要手动迁移
