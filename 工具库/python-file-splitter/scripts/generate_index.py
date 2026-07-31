#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Index Generator
Generates/updates CODE_INDEX.md for a project directory.
Called automatically after any core source file is split or modified.

Usage:
    python generate_index.py <project_dir> [--exclude knowledge_base.py,data.py]
"""

import sys
import os
import io
import re
import ast
import json
import argparse
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# File patterns that are purely knowledge/data, not logic
KNOWLEDGE_PATTERNS = [
    "knowledge_base",
    "kb_",
    "_kb",
    "_data",
    "data_",
    "_dict",
    "dict_",
    "_config",
    "config_",
    "constants",
    "_constants",
]

SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".pytest_cache"
}

SKIP_EXTS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe"}


def is_knowledge_file(filename: str, excluded: list) -> bool:
    name = Path(filename).stem.lower()
    if name in [e.lower() for e in excluded]:
        return True
    for pat in KNOWLEDGE_PATTERNS:
        if pat in name:
            return True
    return False


def analyze_python_file(filepath: Path) -> dict:
    info = {
        "path": str(filepath),
        "type": "python",
        "size_kb": round(filepath.stat().st_size / 1024, 1),
        "functions": [],
        "classes": [],
        "imports": [],
        "exports": [],
        "routes": [],
        "ui_connections": [],
        "description": "",
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                info["functions"].append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef) and node.col_offset == 0:
                info["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef) and node.col_offset == 0:
                info["classes"].append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    mod = node.module.split(".")[0]
                    if not mod.startswith("_"):
                        info["imports"].append(mod)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name.split(".")[0]
                        if not mod.startswith("_"):
                            info["imports"].append(mod)

        # Detect route decorators (Flask/FastAPI style)
        route_pattern = re.compile(r'@(?:app|router|bp)\.(get|post|put|delete|route)\(["\']([^"\']+)')
        for match in route_pattern.finditer(source):
            info["routes"].append(f"{match.group(1).upper()} {match.group(2)}")

        # Detect button/link connections in HTML templates or comments
        # e.g.: # button: 生成报告 -> generate_report()
        conn_pattern = re.compile(r'#\s*(?:button|btn|link|click|onclick)[:：]\s*(.+?)\s*->\s*(.+)', re.IGNORECASE)
        for match in conn_pattern.finditer(source):
            info["ui_connections"].append({
                "trigger": match.group(1).strip(),
                "handler": match.group(2).strip()
            })

        # Extract docstring as description
        if tree.body and isinstance(tree.body[0], ast.Expr):
            val = tree.body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                first_line = val.value.strip().split("\n")[0]
                info["description"] = first_line[:120]

        info["imports"] = sorted(set(info["imports"]))

    except Exception:
        pass
    return info


def analyze_js_file(filepath: Path) -> dict:
    info = {
        "path": str(filepath),
        "type": "javascript",
        "size_kb": round(filepath.stat().st_size / 1024, 1),
        "functions": [],
        "classes": [],
        "imports": [],
        "exports": [],
        "routes": [],
        "ui_connections": [],
        "description": "",
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")

        # Functions
        for m in re.finditer(r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(', source, re.MULTILINE):
            info["functions"].append(m.group(1))

        # Arrow functions / const
        for m in re.finditer(r'^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(', source, re.MULTILINE):
            info["functions"].append(m.group(1))

        # Classes
        for m in re.finditer(r'^(?:export\s+)?class\s+(\w+)', source, re.MULTILINE):
            info["classes"].append(m.group(1))

        # Imports
        for m in re.finditer(r'^import\s+.*?from\s+["\']([^"\']+)["\']', source, re.MULTILINE):
            mod = m.group(1).split("/")[-1].replace(".js", "").replace(".ts", "")
            if not mod.startswith("."):
                info["imports"].append(mod)
            else:
                info["imports"].append(m.group(1))

        # Exports
        for m in re.finditer(r'^export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', source, re.MULTILINE):
            info["exports"].append(m.group(1))

        # Routes (Express style)
        for m in re.finditer(r'(?:app|router)\.(get|post|put|delete)\(["\']([^"\']+)', source):
            info["routes"].append(f"{m.group(1).upper()} {m.group(2)}")

        # UI connections (comment style: // button: xxx -> handler)
        for m in re.finditer(r'//\s*(?:button|btn|link|click|onclick)[:：]\s*(.+?)\s*->\s*(.+)', source, re.IGNORECASE):
            info["ui_connections"].append({
                "trigger": m.group(1).strip(),
                "handler": m.group(2).strip()
            })

        # First comment block as description
        desc_m = re.search(r'/\*\*?\s*\n?\s*\*?\s*([^\n*]+)', source)
        if desc_m:
            info["description"] = desc_m.group(1).strip()[:120]

        info["imports"] = sorted(set(info["imports"]))

    except Exception:
        pass
    return info


def analyze_html_file(filepath: Path) -> dict:
    info = {
        "path": str(filepath),
        "type": "html",
        "size_kb": round(filepath.stat().st_size / 1024, 1),
        "functions": [],
        "classes": [],
        "imports": [],
        "exports": [],
        "routes": [],
        "ui_connections": [],
        "description": "",
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")

        # Extract <title>
        title_m = re.search(r'<title>([^<]+)</title>', source, re.IGNORECASE)
        if title_m:
            info["description"] = title_m.group(1).strip()

        # Buttons and their onclick / data-action
        for m in re.finditer(r'<(?:button|a)[^>]+(?:onclick=["\']([^"\']+)["\']|href=["\']([^"\']+)["\'])[^>]*>([^<]*)<', source, re.IGNORECASE):
            handler = m.group(1) or m.group(2) or ""
            label = m.group(3).strip()
            if label or handler:
                info["ui_connections"].append({
                    "trigger": f"[{label}]" if label else "[button]",
                    "handler": handler.strip()
                })

        # Script src references
        for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', source, re.IGNORECASE):
            info["imports"].append(m.group(1))

        # Link href references
        for m in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\']', source, re.IGNORECASE):
            ref = m.group(1)
            if not ref.startswith("http") and not ref.startswith("//"):
                info["imports"].append(ref)

    except Exception:
        pass
    return info


def analyze_md_file(filepath: Path) -> dict:
    info = {
        "path": str(filepath),
        "type": "markdown",
        "size_kb": round(filepath.stat().st_size / 1024, 1),
        "functions": [],
        "classes": [],
        "imports": [],
        "exports": [],
        "routes": [],
        "ui_connections": [],
        "description": "",
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        lines = source.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                info["description"] = re.sub(r"^#+\s*", "", line)[:120]
                break
    except Exception:
        pass
    return info


def collect_files(project_dir: Path, excluded: list) -> list:
    target_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".md"}
    results = []

    for root, dirs, files in os.walk(project_dir):
        # Prune skip dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith("_module")]
        for f in sorted(files):
            ext = Path(f).suffix.lower()
            if ext in SKIP_EXTS:
                continue
            if ext not in target_exts:
                continue
            full = Path(root) / f
            # Skip knowledge files (they are pure data, no logic routing)
            if ext in {".py", ".js", ".ts", ".jsx", ".tsx"}:
                if is_knowledge_file(f, excluded):
                    continue
            results.append(full)

    return results


def build_dependency_map(all_info: list) -> dict:
    """Build a reverse dependency map: file -> files that import it."""
    # Map short name -> full path
    name_to_path = {}
    for info in all_info:
        stem = Path(info["path"]).stem.lower()
        name_to_path[stem] = info["path"]

    dep_map = {}
    for info in all_info:
        for imp in info.get("imports", []):
            imp_lower = imp.lower().replace("-", "_").replace(".js", "").replace(".ts", "")
            if imp_lower in name_to_path:
                target = name_to_path[imp_lower]
                dep_map.setdefault(target, [])
                if info["path"] not in dep_map[target]:
                    dep_map[target].append(info["path"])

    return dep_map


def generate_markdown(project_dir: Path, all_info: list, excluded: list, dep_map: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    project_name = project_dir.name
    rel = lambda p: os.path.relpath(p, project_dir).replace("\\", "/")

    lines = []
    lines.append(f"# CODE_INDEX — {project_name}")
    lines.append(f"")
    lines.append(f"> Auto-generated by splitter skills. **Do not edit manually.**")
    lines.append(f"> Last updated: {now}")
    lines.append(f"> Core source files: {len(all_info)} | Knowledge/dict files excluded: {', '.join(excluded) if excluded else 'auto-detected'}")
    lines.append("")

    lines.append("## How to Use This Index")
    lines.append("")
    lines.append("When you receive a user instruction, **read this file first** to:")
    lines.append("1. Identify which source file handles the relevant logic")
    lines.append("2. Trace UI button → handler → source file chains")
    lines.append("3. Understand inter-file dependencies before editing")
    lines.append("4. Avoid reading unrelated knowledge/dict files")
    lines.append("")

    # Group by type
    by_type = {}
    for info in all_info:
        t = info["type"]
        by_type.setdefault(t, []).append(info)

    # HTML files first (UI entry points)
    if "html" in by_type:
        lines.append("## UI Entry Points (HTML)")
        lines.append("")
        for info in by_type["html"]:
            p = rel(info["path"])
            desc = info.get("description", "")
            lines.append(f"### `{p}`")
            if desc:
                lines.append(f"**Title:** {desc}")
            lines.append("")
            if info.get("ui_connections"):
                lines.append("**Buttons / Links:**")
                lines.append("")
                lines.append("| UI Element | Action / Handler |")
                lines.append("|:-----------|:----------------|")
                for conn in info["ui_connections"][:30]:
                    trigger = conn["trigger"].replace("|", "\\|")
                    handler = conn["handler"].replace("|", "\\|")[:80]
                    lines.append(f"| {trigger} | `{handler}` |")
                lines.append("")
            if info.get("imports"):
                scripts = [i for i in info["imports"] if i.endswith((".js", ".py", ".ts"))]
                if scripts:
                    lines.append(f"**Linked scripts:** {', '.join(f'`{i}`' for i in scripts)}")
                    lines.append("")
        lines.append("")

    # Python files
    if "python" in by_type:
        lines.append("## Python Source Files")
        lines.append("")
        for info in sorted(by_type["python"], key=lambda x: x["path"]):
            p = rel(info["path"])
            sz = info["size_kb"]
            desc = info.get("description", "")
            lines.append(f"### `{p}` ({sz} KB)")
            if desc:
                lines.append(f"_{desc}_")
                lines.append("")
            # Functions
            if info["functions"]:
                lines.append(f"**Functions:** {', '.join(f'`{f}`' for f in info['functions'][:20])}")
            # Classes
            if info["classes"]:
                lines.append(f"**Classes:** {', '.join(f'`{c}`' for c in info['classes'])}")
            # Routes
            if info["routes"]:
                lines.append(f"**Routes:** {', '.join(info['routes'][:10])}")
            # UI connections (from comments)
            if info["ui_connections"]:
                lines.append("")
                lines.append("**UI Connections (from code comments):**")
                for conn in info["ui_connections"]:
                    lines.append(f"- `{conn['trigger']}` → `{conn['handler']}`")
            # Who imports this file
            abs_p = str(Path(info["path"]).resolve())
            used_by = dep_map.get(info["path"], [])
            if used_by:
                lines.append(f"**Imported by:** {', '.join(f'`{rel(u)}`' for u in used_by)}")
            # What this file imports (local files only)
            local_imports = [i for i in info["imports"] if not i.startswith("_") and len(i) > 1]
            if local_imports:
                lines.append(f"**Imports:** {', '.join(f'`{i}`' for i in local_imports[:15])}")
            lines.append("")

    # JS/TS files
    js_types = [t for t in ("javascript", "typescript") if t in by_type]
    for jt in js_types:
        label = "JavaScript" if jt == "javascript" else "TypeScript"
        lines.append(f"## {label} Source Files")
        lines.append("")
        for info in sorted(by_type[jt], key=lambda x: x["path"]):
            p = rel(info["path"])
            sz = info["size_kb"]
            desc = info.get("description", "")
            lines.append(f"### `{p}` ({sz} KB)")
            if desc:
                lines.append(f"_{desc}_")
                lines.append("")
            if info["functions"]:
                lines.append(f"**Functions:** {', '.join(f'`{f}`' for f in info['functions'][:20])}")
            if info["classes"]:
                lines.append(f"**Classes:** {', '.join(f'`{c}`' for c in info['classes'])}")
            if info["exports"]:
                lines.append(f"**Exports:** {', '.join(f'`{e}`' for e in info['exports'][:15])}")
            if info["routes"]:
                lines.append(f"**Routes:** {', '.join(info['routes'][:10])}")
            if info["ui_connections"]:
                lines.append("")
                lines.append("**UI Connections:**")
                for conn in info["ui_connections"]:
                    lines.append(f"- `{conn['trigger']}` → `{conn['handler']}`")
            used_by = dep_map.get(info["path"], [])
            if used_by:
                lines.append(f"**Imported by:** {', '.join(f'`{rel(u)}`' for u in used_by)}")
            lines.append("")

    # Markdown files (documentation)
    if "markdown" in by_type:
        non_index = [i for i in by_type["markdown"] if Path(i["path"]).name != "CODE_INDEX.md"]
        if non_index:
            lines.append("## Documentation Files")
            lines.append("")
            for info in non_index:
                p = rel(info["path"])
                desc = info.get("description", "")
                lines.append(f"- `{p}`{': ' + desc if desc else ''}")
            lines.append("")

    # Dependency summary
    if dep_map:
        lines.append("## Dependency Map (who imports whom)")
        lines.append("")
        lines.append("| File | Imported By |")
        lines.append("|:-----|:------------|")
        for target, importers in sorted(dep_map.items()):
            t = rel(target)
            imp_str = ", ".join(f"`{rel(i)}`" for i in importers)
            lines.append(f"| `{t}` | {imp_str} |")
        lines.append("")

    lines.append("---")
    lines.append(f"_Index auto-regenerated on every core source file change._")

    return "\n".join(lines)


def generate_index(project_dir: str, excluded: list = None, output_file: str = None) -> str:
    project_path = Path(project_dir).resolve()
    excluded = excluded or []

    if not project_path.exists():
        print(f"Error: directory not found: {project_dir}")
        sys.exit(1)

    print(f"Scanning {project_path} ...")
    files = collect_files(project_path, excluded)
    print(f"Found {len(files)} core source files")

    all_info = []
    for f in files:
        ext = f.suffix.lower()
        if ext == ".py":
            all_info.append(analyze_python_file(f))
        elif ext in {".js", ".ts", ".jsx", ".tsx"}:
            info = analyze_js_file(f)
            info["type"] = "typescript" if ext in {".ts", ".tsx"} else "javascript"
            all_info.append(info)
        elif ext in {".html", ".htm"}:
            all_info.append(analyze_html_file(f))
        elif ext == ".md":
            all_info.append(analyze_md_file(f))

    dep_map = build_dependency_map(all_info)
    md_content = generate_markdown(project_path, all_info, excluded, dep_map)

    out = Path(output_file) if output_file else project_path / "CODE_INDEX.md"
    out.write_text(md_content, encoding="utf-8")
    print(f"CODE_INDEX.md written to: {out}")
    return str(out)


def main():
    parser = argparse.ArgumentParser(description="Generate CODE_INDEX.md for a project directory")
    parser.add_argument("project_dir", help="Project directory to index")
    parser.add_argument("--exclude", default="", help="Comma-separated filenames to treat as knowledge files (no .py needed)")
    parser.add_argument("--output", default="", help="Output path for CODE_INDEX.md (default: <project_dir>/CODE_INDEX.md)")
    args = parser.parse_args()

    excluded = [e.strip() for e in args.exclude.split(",") if e.strip()]
    output = args.output or None
    generate_index(args.project_dir, excluded, output)


if __name__ == "__main__":
    main()
