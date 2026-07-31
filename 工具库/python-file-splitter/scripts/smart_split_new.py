#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Python File Splitter v2.0
Splits large Python files into modules <= 19KB
保留原文件功能的主入口文件生成
"""
import sys
import io

# Fix Windows PowerShell encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import ast
import os
from pathlib import Path
from typing import List, Tuple

MAX_FILE_SIZE = 19 * 1024  # 19KB = 19456字节
MAX_LINES_PER_BLOCK = 300  # 单个代码块最大行数

class PythonFileSplitter:
    def __init__(self, input_file: str, output_dir: str = "modules"):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.modules: List[Tuple[str, str, Path]] = []  # (name, type, path)
        
    def get_file_size(self, file_path: Path) -> int:
        """获取文件大小（字节）"""
        return os.path.getsize(file_path)
    
    def split_large_code_block(self, code_block: str, base_name: str, output_path: Path) -> List[Path]:
        """
        拆分过大的代码块
        策略：按逻辑段落（函数/类定义）分割，保持语法完整性
        """
        try:
            tree = ast.parse(code_block)
        except SyntaxError:
            # 语法解析失败，尝试按行数分割
            return self._split_by_lines(code_block, base_name, output_path)
        
        result_files = []
        
        for node in tree.body:
            node_code = ast.unparse(node) if hasattr(ast, 'unparse') else ""
            node_size = len(node_code.encode('utf-8'))
            
            if node_size > MAX_FILE_SIZE:
                # 当前节点仍然过大，递归拆分
                sub_files = self._split_node_recursive(node, base_name, output_path)
                result_files.extend(sub_files)
            else:
                # 创建单独文件
                node_name = self._get_node_name(node)
                node_type = self._get_node_type(node)
                sub_file = output_path / f"{base_name}_{node_name}.py"
                
                content = f"# Auto-generated: {node_name}\n"
                content += f"# Type: {node_type}\n\n"
                content += node_code
                
                with open(sub_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                result_files.append(sub_file)
                self.modules.append((node_name, node_type, sub_file))
        
        return result_files
    
    def _split_node_recursive(self, node: ast.AST, base_name: str, output_path: Path) -> List[Path]:
        """递归拆分过大的AST节点"""
        node_code = ast.unparse(node) if hasattr(ast, 'unparse') else ""
        node_name = self._get_node_name(node)
        
        if isinstance(node, ast.ClassDef):
            # 类：按方法拆分
            return self._split_class_by_methods(node, base_name, output_path)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 函数：按逻辑段落拆分
            return self._split_function_by_blocks(node, base_name, output_path)
        else:
            # 其他类型节点，直接保存
            sub_file = output_path / f"{base_name}_{node_name}.py"
            content = f"# Auto-generated: {node_name}\n\n{node_code}"
            with open(sub_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return [sub_file]
    
    def _split_class_by_methods(self, class_node: ast.ClassDef, base_name: str, output_path: Path) -> List[Path]:
        """将大类按方法拆分为多个小类"""
        result_files = []
        class_name = class_node.name
        
        # 分离：类属性定义、方法定义
        class_attrs = []
        methods = []
        
        for item in class_node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.AnnAssign, ast.Assign)):
                # 检查是否是属性定义（非函数定义）
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    class_attrs.append(item)
                else:
                    methods.append(item)
            else:
                class_attrs.append(item)
        
        # 为每个方法创建一个小类
        for method in methods:
            method_name = method.name
            sub_class_name = f"{class_name}_{method_name}"
            sub_file = output_path / f"{sub_class_name}.py"
            
            # 创建简化类，只包含一个方法
            sub_class = ast.ClassDef(
                name=sub_class_name,
                bases=[],
                keywords=[],
                body=[method] + class_attrs[:],  # 复制属性
                decorator_list=method.decorator_list
            )
            
            content = f"# Auto-generated from {class_name}.{method_name}\n"
            content += f"# Type: class (method-split)\n\n"
            content += ast.unparse([sub_class]) if hasattr(ast, 'unparse') else ""
            
            with open(sub_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result_files.append(sub_file)
            self.modules.append((sub_class_name, 'class', sub_file))
        
        return result_files
    
    def _split_function_by_blocks(self, func_node: ast.AST, base_name: str, output_path: Path) -> List[Path]:
        """将大函数按逻辑段落拆分为多个函数"""
        result_files = []
        func_name = func_node.name
        func_code = ast.unparse(func_node) if hasattr(ast, 'unparse') else ""
        
        # 尝试按注释段落分割
        blocks = self._extract_logical_blocks(func_code)
        
        for i, block in enumerate(blocks):
            sub_file = output_path / f"{func_name}_part{i+1}.py"
            content = f"# Auto-generated: {func_name} (part {i+1})\n"
            content += f"# Type: function (logical-split)\n\n"
            content += block
            
            with open(sub_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result_files.append(sub_file)
            self.modules.append((f"{func_name}_part{i+1}", 'function', sub_file))
        
        return result_files
    
    def _extract_logical_blocks(self, code: str) -> List[str]:
        """按逻辑段落提取代码块"""
        lines = code.split('\n')
        blocks = []
        current_block = []
        
        for line in lines:
            current_block.append(line)
            
            # 检测段落分隔点：函数定义前、空行后的类/函数定义
            stripped = line.strip()
            if (stripped.startswith('def ') or stripped.startswith('class ') or 
                stripped.startswith('async def ')) and len(current_block) > 10:
                blocks.append('\n'.join(current_block[:-1]))
                current_block = [line]
        
        if current_block:
            blocks.append('\n'.join(current_block))
        
        # 如果分割太少，尝试按行数分割
        if len(blocks) == 1 and len(lines) > MAX_LINES_PER_BLOCK:
            blocks = self._split_by_lines('\n'.join(lines), "block", Path("."))
        
        return blocks
    
    def _split_by_lines(self, code: str, base_name: str, output_path: Path) -> List[Path]:
        """按行数硬分割（保底方案）"""
        lines = code.split('\n')
        result_files = []
        
        for i in range(0, len(lines), MAX_LINES_PER_BLOCK):
            chunk_lines = lines[i:i + MAX_LINES_PER_BLOCK]
            sub_file = output_path / f"{base_name}_chunk{i//MAX_LINES_PER_BLOCK + 1}.py"
            
            content = f"# Auto-generated chunk (lines {i+1}-{i+len(chunk_lines)})\n\n"
            content += '\n'.join(chunk_lines)
            
            with open(sub_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result_files.append(sub_file)
        
        return result_files
    
    def _get_node_name(self, node: ast.AST) -> str:
        """获取AST节点名称"""
        if isinstance(node, ast.FunctionDef):
            return node.name
        elif isinstance(node, ast.AsyncFunctionDef):
            return node.name
        elif isinstance(node, ast.ClassDef):
            return node.name
        elif isinstance(node, ast.Module):
            return "module"
        return "unknown"
    
    def _get_node_type(self, node: ast.AST) -> str:
        """获取AST节点类型"""
        return type(node).__name__
    
    def _extract_main_block(self, tree: ast.AST, source_code: str) -> str:
        """
        从AST中提取 if __name__ == "__main__": 代码块
        返回代码字符串，如果没有则返回空字符串
        """
        for node in tree.body:
            if isinstance(node, ast.If):
                condition = node.test
                if isinstance(condition, ast.Compare):
                    if isinstance(condition.left, ast.Name) and condition.left.id == "__name__":
                        if len(condition.ops) == 1 and isinstance(condition.ops[0], ast.Eq):
                            if len(condition.comparators) == 1:
                                comparator = condition.comparators[0]
                                if isinstance(comparator, ast.Constant) and comparator.value == "__main__":
                                    main_body = ast.unparse(node) if hasattr(ast, 'unparse') else ""
                                    return main_body
        return ""
    
    def _extract_all_imports(self, tree: ast.AST) -> List[str]:
        """从AST中提取所有导入语句"""
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_code = ast.unparse(node) if hasattr(ast, 'unparse') else ""
                if import_code:
                    imports.append(import_code)
        return imports
    
    def _extract_module_docstring(self, tree: ast.AST) -> str:
        """提取模块级别的文档字符串"""
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
                return tree.body[0].value.value
        return ""
    
    def _get_module_exports(self, module_path: Path) -> List[str]:
        """分析模块文件，提取导出的函数名、类名"""
        exports = []
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                code = f.read()
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    exports.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    exports.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            exports.append(target.id)
        except Exception:
            pass
        return exports
    
    def split(self) -> bool:
        """执行拆分主流程"""
        if not self.input_file.exists():
            print(f"❌ 错误: 文件 {self.input_file} 不存在")
            return False
        
        print(f"\n{'='*60}")
        print(f"🔄 智能Python文件拆分器 v2.0")
        print(f"{'='*60}")
        print(f"📄 输入文件: {self.input_file}")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"📏 最大文件大小: {MAX_FILE_SIZE} 字节 ({MAX_FILE_SIZE/1024}KB)")
        print(f"{'='*60}\n")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取源文件
        with open(self.input_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        original_size = len(source_code.encode('utf-8'))
        print(f"📊 源文件大小: {original_size} 字节 ({original_size/1024:.1f}KB)")
        
        # 解析AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"❌ 语法错误: {e}")
            return False
        
        # 分析代码结构
        print("\n📋 代码结构分析:")
        self._analyze_structure(tree)
        
        # 执行拆分
        print("\n🔧 开始拆分...")
        self._split_by_structure(tree, source_code)
        
        # 生成主文件（传递 tree 和 source_code 以保留原功能）
        self._generate_main_file(tree, source_code)
        
        # 生成 __init__.py
        self._generate_init_file()
        
        # 验证文件大小
        print("\n🔍 验证文件大小...")
        violations = self._verify_file_sizes()
        
        # 输出报告
        self._print_report(original_size, violations)
        
        return len(violations) == 0
    
    def _analyze_structure(self, tree: ast.AST):
        """分析代码结构"""
        for node in tree.body:
            name = self._get_node_name(node)
            node_type = self._get_node_type(node)
            size = len(ast.unparse(node).encode('utf-8')) if hasattr(ast, 'unparse') else 0
            
            size_str = f"{size}字节 ({size/1024:.1f}KB)" if size > 0 else "未知"
            warning = " ⚠️ 超过限制" if size > MAX_FILE_SIZE else ""
            
            print(f"  • {node_type}: {name} ({size_str}){warning}")
    
    def _split_by_structure(self, tree: ast.AST, source_code: str):
        """按代码结构拆分"""
        all_nodes = list(tree.body)
        
        # 按函数/类分组
        current_file_nodes = []
        current_file_size = 0
        file_index = 0
        
        for node in all_nodes:
            node_code = ast.unparse(node) if hasattr(ast, 'unparse') else ""
            node_size = len(node_code.encode('utf-8'))
            
            # 如果单个节点就超过限制，需要特殊处理
            if node_size > MAX_FILE_SIZE:
                # 先保存当前累积的文件
                if current_file_nodes:
                    self._write_module_file(file_index, current_file_nodes, all(current_file_nodes))
                    file_index += 1
                    current_file_nodes = []
                    current_file_size = 0
                
                # 处理超大节点
                self._handle_large_node(node, file_index)
                file_index += 1
            elif current_file_size + node_size > MAX_FILE_SIZE:
                # 当前文件要超限，写入并新建
                if current_file_nodes:
                    self._write_module_file(file_index, current_file_nodes, all(current_file_nodes))
                    file_index += 1
                current_file_nodes = [node]
                current_file_size = node_size
            else:
                current_file_nodes.append(node)
                current_file_size += node_size
        
        # 处理剩余节点
        if current_file_nodes:
            self._write_module_file(file_index, current_file_nodes, all(current_file_nodes))
    
    def _write_module_file(self, index: int, nodes: List[ast.AST], is_last: bool):
        """写入模块文件"""
        module_name = f"module_{index:03d}"
        module_file = self.output_dir / f"{module_name}.py"
        
        content = f"# Auto-generated module {index}\n"
        content += f"# Source: {self.input_file.name}\n\n"
        
        for node in nodes:
            content += ast.unparse(node) + "\n\n" if hasattr(ast, 'unparse') else ""
        
        with open(module_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.modules.append((module_name, 'module', module_file))
        print(f"  ✓ 生成: {module_file.name}")
    
    def _handle_large_node(self, node: ast.AST, index: int):
        """处理超大节点"""
        node_name = self._get_node_name(node)
        node_type = self._get_node_type(node)
        node_code = ast.unparse(node) if hasattr(ast, 'unparse') else ""
        
        print(f"  ⚠️  {node_type} '{node_name}' 过大，开始智能拆分...")
        
        # 按子节点拆分
        if isinstance(node, ast.ClassDef):
            sub_files = self._split_class_by_methods(node, node_name, self.output_dir)
            for sf in sub_files:
                self.modules.append((sf.stem, 'class', sf))
        else:
            sub_files = self._split_function_by_blocks(node, node_name, self.output_dir)
            for sf in sub_files:
                self.modules.append((sf.stem, 'function', sf))
        
        print(f"    ✓ 拆分为 {len(sub_files)} 个文件")
    
    def _generate_main_file(self, tree: ast.AST = None, source_code: str = ""):
        """生成主入口文件 - 与原文件同名，保留原功能"""
        main_file = Path(self.input_file.stem + ".py")
        
        # 提取原文件的关键信息
        original_imports = self._extract_all_imports(tree) if tree else []
        main_block = self._extract_main_block(tree, source_code) if tree else ""
        module_docstring = self._extract_module_docstring(tree) if tree else ""
        
        # 构建主文件内容
        content_parts = []
        
        # 1. 文件头
        content_parts.append(f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""")
        
        # 2. 文档字符串（保留原文件的模块文档）
        if module_docstring:
            content_parts.append(f'"""\n{module_docstring}\n"""\n')
        else:
            content_parts.append(f""""""
{main_file}
由 python-file-splitter 自动生成
保留原文件功能的入口文件
"""\n""")
        
        # 3. 添加 sys.path 处理，确保模块能正确导入
        content_parts.append("""import sys
import os

# 添加当前目录到路径，确保模块可导入
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

""")
        
        # 4. 保留原文件的导入语句（过滤掉相对导入）
        if original_imports:
            content_parts.append("# 原文件导入\n")
            for imp in original_imports:
                # 跳过相对导入，因为模块结构已改变
                if not imp.startswith("from ."):
                    content_parts.append(imp + "\n")
            content_parts.append("\n")
        
        # 5. 添加模块目录导入
        content_parts.append(f"# 从拆分模块导入\n")
        content_parts.append(f"sys.path.insert(0, os.path.join(_current_dir, '{self.output_dir.name}'))\n")
        content_parts.append(f"from {self.output_dir.name} import *\n\n")
        
        # 6. 显式导入各模块的内容
        content_parts.append("# 模块内容导入\n")
        for name, module_type, path in self.modules:
            exports = self._get_module_exports(path)
            if exports:
                # 只导入公共名称（非下划线开头）
                public_exports = [e for e in exports if not e.startswith('_')]
                if public_exports:
                    content_parts.append(f"from {self.output_dir.name}.{path.stem} import {', '.join(public_exports[:5])}\n")
        
        content_parts.append("\n")
        
        # 7. 保留原文件的 main 块，或生成默认入口
        if main_block:
            content_parts.append("# 原文件入口点\n")
            content_parts.append(main_block)
            content_parts.append("\n")
        else:
            content_parts.append("""# 默认入口点
if __name__ == "__main__":
    print(f"由 python-file-splitter 自动生成: {__file__}")
    print("请检查模块是否正确导入并调用")
""")
        
        # 写入文件
        content = "".join(content_parts)
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✓ 生成主文件: {main_file}")
        if main_block:
            print(f"  ✓ 已保留原文件的 __main__ 执行逻辑")
        else:
            print(f"  ⚠️  原文件没有 __main__ 块，生成默认入口")
    
    def _generate_init_file(self):
        """生成 __init__.py"""
        init_content = "# -*- coding: utf-8 -*-\n"
        init_content += '"""\n'
        init_content += f"{self.output_dir.name} package\n"
        init_content += f"Auto-generated from {self.input_file.name}\n"
        init_content += '"""\n\n'
        init_content += "import sys\n"
        init_content += "import os\n\n"
        init_content += "# Ensure correct package path\n"
        init_content += "__all__ = [\n"
        
        for name, _, path in self.modules:
            init_content += f"    '{path.stem}',\n"
        
        init_content += "]"
        
        init_file = self.output_dir / "__init__.py"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        print(f"✓ 生成包初始化: {init_file.name}")
    
    def _verify_file_sizes(self) -> List[Tuple[str, int]]:
        """验证所有文件大小"""
        violations = []
        
        for module_name, _, path in self.modules:
            size = self.get_file_size(path)
            if size > MAX_FILE_SIZE:
                violations.append((path.name, size))
        
        return violations
    
    def _print_report(self, original_size: int, violations: List[Tuple[str, int]]):
        """输出拆分报告"""
        print(f"\n{'='*60}")
        print(f"📊 拆分报告")
        print(f"{'='*60}")
        print(f"📄 源文件: {self.input_file.name} ({original_size/1024:.1f}KB)")
        print(f"📁 生成模块: {len(self.modules)} 个")
        print(f"📏 所有文件 ≤19KB: {'✅ 是' if not violations else '❌ 否'}")
        
        if violations:
            print(f"\n⚠️  超过限制的文件:")
            for name, size in violations:
                print(f"  - {name}: {size}字节 ({size/1024:.1f}KB)")
        
        print(f"{'='*60}")
        print(f"🎉 拆分完成!")
        print(f"\n使用方式:")
        print(f"  python {self.input_file.stem}.py")
        print(f"{'='*60}")


def main():
    if len(sys.argv) < 2:
        print("用法: python smart_split.py <输入文件> [输出目录]")
        print("示例: python smart_split.py my_script.py modules")
        print("\n功能说明:")
        print("  • 按函数/类逻辑拆分Python文件")
        print("  • 确保每个文件 ≤19KB")
        print("  • 超大函数/类自动二次拆分")
        print("  • 自动生成导入关系和入口文件")
        print("  • 保留原文件的 __main__ 执行逻辑")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "modules"
    
    splitter = PythonFileSplitter(input_file, output_dir)
    success = splitter.split()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
