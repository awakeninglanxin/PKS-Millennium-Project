# GDV项目自动验证

验证 `sunburst_html.py` / `generate_all_charts.py` 等修改后生成产物正确性。

## 触发词
"验证一下"、"验证"、"自动验证"、"跑验证"、"check"、"verify"

## 执行步骤

### 必做：先读架构索引（铁律65）
```
读 D:\AAA我的文件\bio-well csv报告\GDV专业分析报告\架构索引网络.md §6 三层验证流程
```

### 执行验证脚本
```bash
cd "D:/AAA我的文件/bio-well csv报告/GDV专业分析报告"
"D:/Program Files/Python312/python.exe" _auto_verify.py
```

### 如果需要重新生成HTML后再验证
```bash
cd "D:/AAA我的文件/bio-well csv报告/GDV专业分析报告"
"D:/Program Files/Python312/python.exe" _auto_verify.py --generate
```

## 验证项（9项）
| # | 检查项 | 方法 |
|---|--------|------|
| ① | Python语法 | `py_compile` 全部biowell/ + 根目录关键py |
| ② | f-string括号平衡 | `{{` `}}` 计数差值=0 |
| ③ | (可选)重新生成HTML | `generate_all_charts.py` |
| ④ | JS语法 | `node --check` 提取script块 |
| ⑤ | 关键函数存在性 | grep: renderBehaviorTable/drawMarvelSunburst/mergeSunburstData/toggleLiteMode/applyMeridians/buildLiteAnalysis/showMeasurement |
| ⑥ | 关键数据注入 | grep: mer_deltas/_is_summary/BEHAVIOR_DATA/SUNBURST_DATA/ALL_SUMMARY/MERIDIAN_NAMES |
| ⑦ | HTML文件大小 | 正常范围 >5MB |
| ⑧ | 闭包属性调用完整性 | 检测JS闭包内属性方法是否误用裸名（铁律67） |
| ⑨ | COLS数据键与renderPage一致性 | 检测COLS数组字段名与renderPage读取字段是否匹配 |

## 注意事项
- 验证脚本放在项目根目录 `_auto_verify.py`
- 验证完若有错误(`exit 1`)则**禁止跳过**，必须逐项修复
- 验证通过才能对用户说"完成"
