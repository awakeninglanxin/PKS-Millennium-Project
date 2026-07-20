---
name: mylove-quick-ref
description: 蓝馨项目速查卡 — 每次任务启动时必须加载的铁律速查与行动规范。触发词极广：编程、代码、任务、项目、开始工作、干活、csv、bio-well、报告、图表、matplotlib、表格、md、说明、html、py、更新、修改、修复、bug、一键更新、bat、铁律、soul。几乎所有任务启动时应自动触发此技能，确保不犯低级错误。
agent_created: true
---

# 蓝馨项目速查卡

> 每次开始任务前快速过一遍，确保不踩坑。

## 行动指令

1. **只增不删，删需授权** — 禁止擅自删除原功能，只能增量。除非老师明确允许。
2. **先读说明，后动手** — 干活前先读完相关目录的所有 `*说明.md`，不了解项目历史不得开干。
3. **改完验bat，防回退** — 功能改完后，运行 `AAA一键更新报告.bat` 并逐个检查主界面每个功能，确认没被覆盖回原形。
4. **改功能 → 同步更新说明.md** — 新增/修改功能后，主动找出所有应更新的 `*说明.md` 并完善。
5. **踩坑 → 写入铁律** — 任何低级错误总结记入 SOUL.md 铁律。必要时同步更新相关 skill。
6. **不确定先问，不盲动** — 遇到不清楚的地方先问老师，不要猜着干。
7. **导出迭代历史.md** — 每轮重大项目变更后导出项目进化历史，此后自动优先读此文件。
8. **回复末附预判任务** — 每次回复最后列出预判下一步要做的任务，格式：`预判任务：1.xxx 2.xxx 3.xxx`
9. **预判必须先grep验证** — 下发预判任务前必须 `grep` 确认目标文件确实存在相关列/字段/变量。禁止假设"应该有"就写进预判。误判一次，少一份信任。

## 专业指令

9. **md表格/编码 → 必调ima编码技能** — 涉及 .md 表格生成或 .bat/.ps1 创建时，先加载 `ima-markdown-table` 和 `windows-encoding` 技能。
10. **plt出图 → 必设SimHei字体** — 调用 matplotlib 画图时必须在代码中设置：
    ```python
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    ```
    否则中文标签显示为白板/方框。
11. **图表覆盖/错位 → 查 dispose + v-if + z-index** — 网页切换触发图表互相覆盖时：① 销毁 ECharts 实例(dispose) ② 条件渲染(v-if)卸载组件 ③ CSS z-index。先用 DevTools 看 DOM 是否"脏"。
12. **遇难题 → IMA知识库 + DS深度思考**

## 固定路径

```
CSV测量文件：C:\Users\ThinkPad\Desktop\bio-well csv报告\蓝馨\csv多次报告数据库
一键更新bat：C:\Users\ThinkPad\Desktop\bio-well csv报告\蓝馨\AAA一键更新报告.bat
GDV报告目录：C:\Users\ThinkPad\Desktop\bio-well csv报告\GDV专业分析报告
蓝馨完整手册：C:\Users\ThinkPad\Desktop\bio-well csv报告\蓝馨\说明md\蓝馨项目完整手册_合一版.md
```

## 速查口诀

```
只增不删 → 先读说明 → 改完验bat → 同步更新.md → 踩坑记铁律
→ plt设SimHei → md调ima编码 → 回复附预判 → 不确定先问 → 导出迭代历史.md
```

## 关键铁律（来自SOUL.md）

- **铁律1**：永远改 .py 源码，绝不手动改 HTML/MD 输出
- **铁律2**：绝不删除原版已有功能
- **铁律4**：不硬编码修复，改源头 .py
- **铁律5**：CSV 分隔符永远是 `;`
- **铁律6**：修改含 .py/.js 目录下的文件前，必须先向上搜索 `*说明.md`
- **铁律8**：f-string `{{}}` 内 JS onclick 引号必须用 `&quot;`
- **铁律10**：修改 CSV 前必须先备份
- **铁律13**：删除文件必须进回收站，禁止 rm/os.remove
- **铁律21**：Windows 中文环境下写文件前，先确认消费者编码格式
- **铁律24**：plt 画图必须设中文字体
- **铁律25**：生成 MD 表格/脚本文件必须触发对应技能（ima-markdown-table / windows-encoding）
- **铁律45**：修改 sunburst_html.py / chakra_ann_table.py 后必须 run `check_js.bat`。`node --check` 全自动，防 JS 引号/括号错误导致整页白屏
- **铁律46**：`--only-md` 必须双重守卫（函数调用 + `open(...,'w')` 文件写入 + 注入操作），仅加 `SKIP_HTML_ALL` 函数调用不够——后续 `open(...,'w')` 仍覆写文件
- **铁律47**：JS `html += '...'` 单引号字符串内禁用裸单引号属性值。`onfocus="this.placeholder=''"` 中的 `''` 会提前闭合 JS 字符串 → SyntaxError → 白屏
- **铁律61**：修改 JS 数据 pipeline 后必须 g rep 全部下游 `.toFixed()` / 字段引用，确认 pipeline 输出包含所有消费字段。仅看签名不够——`undefined.toFixed()` 在 runtime 才炸。
- **铁律62**：遇到需写工具脚本时，先查 `D:\软件必备\workbuddy建的py工具\` 是否有现存工具可用。没有就自己写，完成后备份最新版到此目录。bat文件在中文Windows必须GBK+CRLF（可用 `fix_bat_gbk.py` 修复）。

## WorkBuddy Py工具清单

`D:\软件必备\workbuddy建的py工具\` 目录持续维护，按需取用：

| 工具名 | 用途 |
|--------|------|
| `fix_bat_gbk.py` | 修复 bat 文件编码为 GBK+CRLF，防中文路径闪退 |
| `parse_nls_pcap.py` | USB pcap 抓包解析 NLS 128字节指令 |
| `send_therapy_v1.py` | COM4 发送治疗命令到手环 |
| `analyze_v1.py` | V1 Z-score 异常诊断分析 |
| `map_30items_to_families.py` | 器官异常 → M集25族频率映射 |
| `xch_parver.py` | XCH 检测文件 → CSV 转换 |
| `gen_audio_v4.py` | 分形波形 → WAV 音频生成 |
| `gen_binaural_v2.py` | 双耳节拍音频生成 |
| `batch_audio.py` | 批量音频生成 |
| `fractal_waveform.py` | M集分形波形算法类 |
| `bubble_freq_mapper.py` | M集气泡频率映射 |

## HTML生成步骤完整清单

| Step | 文件名 | 函数调用 | 文件写入 |
|------|--------|---------|---------|
| 1 | jingluo_short/organ_short/气场等 | generate_reports() | 内部open |
| 1b | 每次的能量扫描分析 | generate_energy_scan() | 内部open |
| 2 | 能量层次旭日图 | SKIP_SUNBURST | generate_sunburst_html() |
| 6 | 脉轮分析报告 | generate_chakra_report_from_csv() | open(chakra_path,'w')注入 |
| 7 | 九型人格 | generate_comprehensive_enneagram_report() | open(enneagram_html_path,'w') |
| 8 | 6号与8号快速评估问卷 | generate_enneagram_6_8_questionnaire() | 内部open |
| 10 | 短期趋势报告 | short_term.run() | 内部open |
| 10a | 身心性法四套系统 | _generate_four_systems_page() | 内部open |
| 11 | 主界面 | generate_main_dashboard() | 内部open |
| 11b | 电路理论公式 | generate_circuit_formula_page() | 内部open |

## 修改流程

1. **改前读备份** — 不确定时先 `cp file.py file.py.bak`
2. **f-string 括号双写** — JS/CSS 的 `{` `}` → `{{` `}}`
3. **JS 引号检查** — `html += '...'` 内不用裸 `'`
4. **改后跑 check_js.bat** — 涉及 JS 必须验证
5. **改后跑 --only-md** — 验证所有 `[SKIP]` 日志
6. **改后跑 --skip-sunburst** — 验证非JS模块
7. **最后跑完整版** — 595旭日图全量验证
8. **同步备份** — `GDV+soul铁律方法论文档\`
