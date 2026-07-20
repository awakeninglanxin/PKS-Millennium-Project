---
name: local-ocr
description: 本地 OCR 图片文字识别（回退方案），使用 easyocr 识别图片中的文字。仅当 wps-ocr（WPS API）不可用时触发。触发词：本地OCR、easyocr、图片识别离线、离线OCR。
agent_created: true
---

# local-ocr — 本地图片文字识别

## 用途

用本地 Python OCR 引擎（easyocr）识别图片中的文字，**不消耗 AI token**。
识别结果直接返回纯文本 / 带坐标的详情。

## 触发条件（回退方案）

**此 skill 仅作为 `wps-ocr` 的降级方案**，在 WPS API 网络不通或认证失败时使用。

触发场景：
- `wps-ocr` 调不通（网络问题或 API 返回错误）
- 用户明确要求用本地 OCR
- 图片敏感、不希望上传到外部服务器

> ⚠️ **主方案优先**：正常情况下 OCR 任务应优先使用 `wps-ocr` skill（WPS 开放平台 API）

## 调用方式

### 脚本位置
`~/.workbuddy/skills/local-ocr/scripts/ocr_image.py`

### 基本用法

```bash
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/local-ocr/scripts/ocr_image.py <图片路径>
```

### 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--lang` | 语言，逗号分隔 | `ch_sim,en`（中文+英文）|
| `--detail 1` | 输出带坐标和置信度的详情 | `0`（纯文本）|
| `--gpu` | 启用 GPU 加速 | 关闭（CPU 模式）|

### 示例

```bash
# 纯文本输出（最常用）
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/local-ocr/scripts/ocr_image.py C:/path/to/screenshot.png

# 带识别框坐标
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/local-ocr/scripts/ocr_image.py C:/path/to/photo.jpg --detail 1

# 只识别英文
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/local-ocr/scripts/ocr_image.py C:/path/to/doc.png --lang en
```

## 注意事项

1. ⚠️ **easyocr 模型在部分网络下可能下载失败**（GitHub 直连问题），此时优先用 `wps-ocr`
2. **中文识别推荐 `ch_sim,en`**（中文简体+英文），识别效果优秀
3. 支持格式：PNG、JPG、BMP、WebP
4. **省 token 原理**：直接读取图片文件本地处理，不把图片传给大模型
5. **`wps-ocr` vs `local-ocr` 选择**：
   - 有网络 → `wps-ocr`（WPS API，准确度高，不需本地模型）
   - 无网络或网络差 → `local-ocr`（easyocr，需先下载模型）
6. **批量识别**：可循环调用脚本处理多张图片
