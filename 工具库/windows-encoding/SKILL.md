---
name: windows-encoding
description: >
  Guide for Windows Chinese file encoding pitfalls. Covers bat(.bat/.cmd=GBK+CRLF),
  PowerShell(.ps1=UTF-8 BOM+LF), and general encoding rules for Chinese Windows
  systems. Triggers when creating/modifying Windows script files that may encounter
  encoding issues, or when the user mentions GBK/UTF-8/CRLF/ANSI encoding problems
  on Chinese Windows.
agent_created: true
---

# Windows File Encoding for Chinese Systems

## When to Use This Skill

This skill should be used when:
- Creating or modifying `.bat` / `.cmd` files on Chinese Windows
- Creating or modifying `.ps1` files for Windows PowerShell 5.1
- Writing Python code that creates Windows script files
- The user reports garbled Chinese text, title bars showing random characters, or batch files flashing and closing
- Any task involving file encoding decisions on a Chinese Windows system

## Encoding Reference Table

| Consumer | File Type | Encoding | Line Endings | Notes |
|---|---|---|---|---|
| cmd.exe | `.bat` `.cmd` | ANSI/GBK | `\r\n` CRLF | CRITICAL: UTF-8 causes garbled Chinese + command corruption |
| PowerShell 5.1 | `.ps1` | UTF-8 with BOM (EF BB BF) | `\n` LF | Without BOM → Chinese garbled |
| PowerShell 7+ (pwsh) | `.ps1` | UTF-8 without BOM | `\n` LF | PS7 defaults to UTF-8, no BOM needed |
| Python | `.py` `.json` `.csv` | UTF-8 without BOM | `\n` LF | PEP 8 standard |

## Win11 注意事项

Win11 引入了 Beta UTF-8 全局化选项（`设置 → 时间和语言 → 语言和区域 → 管理语言设置 → 使用Unicode UTF-8提供全球语言支持`），开启后 CMD 可读 UTF-8 的 bat 文件。

**结论：不要依赖此选项。** 绝大多数企业/默认环境未开启，继续使用 GBK 策略是最大兼容性选择，直到确认目标机器全部运行 PowerShell 7。

## Correct File Writing Approaches

### Python: Write a bat/ps1 file with proper encoding

```python
# Write bat (GBK + CRLF)
with open('script.bat', 'w', encoding='gbk') as f:
    f.write(content_with_crlf)

# Write ps1 for PowerShell 5.1 (UTF-8 BOM + LF)
import codecs
with codecs.open('script.ps1', 'w', encoding='utf-8-sig') as f:
    f.write(content)

# Write ps1 for PowerShell 7+ (UTF-8 no BOM + LF)
with open('script.ps1', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

# Safer: write raw bytes for complete control
bat = b'@echo off\r\n'
bat += b'title ' + '标题'.encode('gbk') + b'\r\n'
bat += b'pause >nul\r\n'
with open('script.bat', 'wb') as f:
    f.write(bat)
```

### PowerShell: Write files with proper encoding

```powershell
# Write ps1 (UTF-8 with BOM) for PS 5.1
[System.IO.File]::WriteAllText(
    "C:\path\file.ps1",
    $scriptContent,
    (New-Object System.Text.UTF8Encoding $true)
)

# Write bat (ANSI/GBK)
[System.IO.File]::WriteAllText(
    "C:\path\file.bat",
    $batContent,
    [System.Text.Encoding]::Default
)
```

## VS Code Project Settings (Recommended — Automates Encoding Rules)

Instead of relying on manual discipline, lock encoding rules into the project via `.vscode/settings.json`:

```json
{
    "files.associations": {
        "*.bat": "bat",
        "*.cmd": "bat"
    },
    "[bat]": {
        "files.encoding": "gbk",
        "files.eol": "\r\n"
    },
    "[powershell]": {
        "files.encoding": "utf8bom",
        "files.eol": "\n"
    },
    "[python]": {
        "files.encoding": "utf8",
        "files.eol": "\n"
    }
}
```

Team members using VS Code will automatically save files with the correct encoding — no manual checks needed.

## General Decision Workflow

1. Identify the **consumer** of the file (cmd.exe / PowerShell 5.1 / PowerShell 7 / Python / etc.)
2. Look up the required **encoding** and **line ending** from the reference table
3. Write using the appropriate method from the examples above
4. Never assume UTF-8 without BOM is safe — for cmd.exe it is **guaranteed** to fail with Chinese text

## Common Failure Patterns

| Symptom | Root Cause | Fix |
|---|---|---|
| Title bar shows `WiFi啼鏌3涑錯4` | bat is UTF-8, cmd reads as GBK | Rewrite bat as GBK+CRLF |
| `'鍣?powershell' not recognized` | UTF-8 bytes before `powershell` corrupt cmd parsing | Rewrite bat as GBK+CRLF |
| Script window opens and immediately closes | Base64 > 8191 chars in one bat line | Split into multiple `set "V=..."` lines, or use bat→ps1 separated approach |
| `Select-String '关键内容'` returns nothing | Chinese text corrupted through PowerShell pipe | Use XML export + XPath instead of parsing Chinese text |
| XML file `WLAN 3-1001.xml` not found | Hardcoded filename expects `1001.xml` | Use `Get-ChildItem -Filter "*.xml" \| Sort LastWriteTime -Desc \| Select -First 1` |
| Chinese garbled in echo even when bat is GBK | `chcp 65001` in bat changes console to UTF-8, conflicting with GBK file encoding | **Do NOT put `chcp 65001` in GBK bat files** — use default 936 codepage |

## Bat + Ps1 Separation Pattern (Recommended)

Instead of embedding complex PowerShell in base64 inside bat, separate:

```
script_folder/
├── run.bat           # GBK+CRLF, just 3 lines: @echo off, call ps1, pause
└── logic.ps1         # UTF-8 BOM+LF, all real logic here
```

### run.bat (GBK + CRLF)

```bat
@echo off
chcp 936 > nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0logic.ps1"
pause
```

> `chcp 936 > nul` — 主动设置 GBK 代码页，防止用户系统改过区域设置导致乱码。

### logic.ps1 (UTF-8 BOM + LF, for PowerShell 5.1)

```powershell
#Requires -Version 5.1

# Set console output to UTF-8 (affects PS output only, not the bat)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Your business logic here
Write-Host "中文测试通过" -ForegroundColor Green
```

This avoids all base64 truncation, encoding, and escaping issues.

### If target environment has PowerShell 7 (pwsh)

Replace the bat call with:

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0logic.ps1"
```

And save `logic.ps1` as UTF-8 **without** BOM.

## Related Skills and Iron Rules

- **ima-markdown-table skill**: 当生成含表格的 .md 文件（可能由 bat 脃本生成）时，需同时遵守 IMA 7 规
- **SOUL.md 铁律 18**: bat+ps1 分离模式（已踩坑，闪退）
- **SOUL.md 铁律 21**: Windows 编码三角（GBK/UTF-8 BOM/UTF-8 no-BOM）
- **SOUL.md 铁律 24**: matplotlib 中文出图字体设置
- **SOUL.md 铁律 25**: 生成文件前必须触发对应编码技能
