# ocr-rename — Win原生OCR批量自动重命名图片

## 功能

使用 Windows 内置 OCR 识别图片中的文字，自动根据内容批量重命名图片文件。

**免上传、免token、免网络** — 全程本地 Windows RT OCR，不消耗任何 API 额度。

## 触发条件

- 用户有大量截图/图片需要根据内容重命名
- 用户说"识别这些图片然后改名" / "OCR重命名" / "根据图片内容自动命名"
- 用户拖入/指定一个包含未命名图片的文件夹

## 调用方式

```bash
# 预览模式（不实际改名）
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/ocr-rename/ocr_rename.py 目标目录 --dry-run

# 实际执行
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/ocr-rename/ocr_rename.py 目标目录

# 带前缀
"D:/Program Files/Python312/python.exe" ~/.workbuddy/skills/ocr-rename/ocr_rename.py 目标目录 --prefix "蛋形_"
```

## 技术原理

1. PIL 打开图片 → 转 PNG bytes（内存中，不写磁盘）
2. `InMemoryRandomAccessStream` 将 bytes 送入 WinRT OCR 引擎
3. 绕过中文路径兼容问题（不需要 StorageFile API）
4. 取 OCR 第一行有意义文字作为文件名
5. 自动去重（文件名冲突时加 _2, _3 后缀）

## 局限

- OCR 质量取决于图片清晰度和文字密度
- 软件界面截图（满是按钮）会产生低质量文件名
- 建议先 `--dry-run` 预览再实际执行
