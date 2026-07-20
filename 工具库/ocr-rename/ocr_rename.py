#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocr-rename — Windows原生OCR批量重命名图片
===========================================
使用 WinRT OCR（通过 InMemoryRandomAccessStream 绕过中文路径），
识别图片文字后自动根据内容重命名文件。

调用方式:
  python ocr_rename.py 目标目录  [--dry-run]  [--prefix 前缀]

铁律: OCR默认用Win原生，免上传免token。
依赖: 复用 wps-ocr skill 的 win_ocr_sync 函数。
"""

import os, sys
from pathlib import Path

# 复用 wps-ocr skill 的 Win OCR 函数
sys.path.insert(0, os.path.expanduser(r'~\.workbuddy\skills\wps-ocr\scripts'))
from wps_ocr import win_ocr_sync


def safe_filename(text, max_len=45):
    """OCR文字 → 安全文件名。取第一行有意义的文字。"""
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) >= 2]
    if not lines:
        return None
    name = lines[0]
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, '')
    name = name.strip()
    if not name or len(name) < 2:
        return None
    return name[:max_len]


def batch_rename(target_dir, dry_run=False, prefix=''):
    """扫描目录下所有图片，OCR识别后重命名。"""
    target = Path(target_dir)
    if not target.is_dir():
        print(f'[ERROR] 目录不存在: {target_dir}')
        return

    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    images = sorted([f for f in target.iterdir()
                     if f.suffix.lower() in exts and f.is_file()])

    if not images:
        print('未找到图片文件。')
        return

    print(f'找到 {len(images)} 张图片，正在 OCR 识别...\n')
    renamed = 0; skipped = 0

    for i, img in enumerate(images, 1):
        print(f'[{i:2d}/{len(images)}] {img.name[:50]}', end=' ')
        sys.stdout.flush()

        text, src, ms = win_ocr_sync(str(img))

        if not text or src.startswith('win_noengine') or src.startswith('win_err'):
            status = src.replace('win_', '')
            print(f'→ SKIP ({status})')
            skipped += 1
            continue

        name = safe_filename(text)
        if name is None:
            # 尝试用第二行作为文件名
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) >= 2]
            name = safe_filename('\n'.join(lines[1:])) if len(lines) > 1 else None

        if name is None:
            print(f'→ SKIP (无有效文字)')
            skipped += 1
            continue

        new_name = f'{prefix}{name}{img.suffix}'
        new_path = target / new_name

        c = 2
        while new_path.exists():
            stem = target / f'{prefix}{name}' if prefix else target / name
            new_path = target / f'{stem.name}_{c}{img.suffix}'
            c += 1

        if dry_run:
            print(f'→ [DRY] {new_path.name[:45]}')
        else:
            img.rename(new_path)
            print(f'→ {new_path.name[:45]}')
        renamed += 1

    print(f'\n完成: {renamed} 已重命名, {skipped} 跳过.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Win原生OCR批量重命名图片')
    parser.add_argument('directory', help='目标目录')
    parser.add_argument('--dry-run', action='store_true', help='仅预览不实际改名')
    parser.add_argument('--prefix', default='', help='文件名前缀')
    args = parser.parse_args()
    batch_rename(args.directory, dry_run=args.dry_run, prefix=args.prefix)
