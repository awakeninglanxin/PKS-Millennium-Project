---
name: gene-card-ocr
description: 基因卡片OCR识别 — 从长图截图批量提取1028个基因卡片的结构化数据(基因名/位置/染色体/器官/系统)。支持追加新卡片, 自动复用OCR缓存。
agent_created: true
---

# 基因卡片OCR识别 Skill

## 触发词
识别基因卡片、追加基因数据、基因截图OCR、卡片补全、基因卡片识别

## 工具目录
`D:\AAA我的文件\中健国康 NLS细胞检测\华医公司规划\基因卡片OCR工具\`

## 文件清单
- `extract_cards.py` — 主脚本(已吸收全部13个坑点), 可直接运行
- `gene_ocr_cache.json` — OCR缓存(42张图文字块坐标, 719KB)
- `merge_new_cards.py` — 辅助: 新卡片合并脚本
- `README.md` — 使用说明

## 追加新卡片流程
1. 用户将新截图放入 `截图/请按时间排序查看/`
2. 运行 `extract_cards.py` 主函数, 自动复用缓存
3. 输出到 `基因片段数据库_1028_最终版.xlsx`
4. 检查空值, 用缓存补全

## 脚本已修复的13个坑点

| # | 坑 | 修复方案 |
|---|----|---------|
| 1 | OpenCV不支持中文路径 | 全程用PIL替代OpenCV |
| 2 | 逐卡OCR太慢(1028次) | 全图分段OCR一次, 行聚类分配 |
| 3 | 基因名系统性错位 | 文字块按Y中心聚类成"行", 编号与基因名同行自然归属 |
| 4 | Gene_Name空值46个 | 放宽匹配: 允许"未知"/中文/含数字 |
| 5 | Gene_Location漏"X中间" | 正则扩展: d+中间 + d+[A-Z]+中间 |
| 6 | OCR杂音($ _前缀) | 自动清理 |
| 7 | Chromosome浮点数(1.0) | 转int字符串 |
| 8 | 超长图(28744px)文字丢失 | 分段OCR ≤3500px + 200px重叠 |
| 9 | HuggingFace被墙 | HF_ENDPOINT=https://hf-mirror.com |
| 10 | cnstd缺PP-OCRv6模型 | 改用 PP-OCRv3_det |
| 11 | Excel文件占用 保存失败 | 自动换名另存 |
| 12 | 重复卡片 | Card_ID去重 |
| 13 | 新图重复OCR | JSON缓存复用 |

## OCR引擎
- cnocr + PP-OCRv3_det + densenet_lite_136-gru
- 行聚类阈值: ROW_THRESHOLD=25px
- 分段OCR: 每段3500px + 200px重叠

## Gene_Location正则(已完整)
```
\d+[左右]\d+          # 1左6, 17右4
\d+中间               # 1中间, 2中间
\d+[A-Z]+中间         # 23X中间, 23Y中间
```

## 当前数据
- 1028条 #1~#1028, 7列100%, 零空值
- 最终文件: `基因片段数据库_1028_最终版.xlsx`
