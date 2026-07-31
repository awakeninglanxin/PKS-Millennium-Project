#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md-typora-fix — 修复MD文件中公式内的中文/英文标签为Typora兼容格式

规则：
  - $$...$$ 和 $...$ 内的中文 → 用 \text{中文} 包裹
  - $$...$$ 和 $...$ 内的英文多字母下标 → 用 \text{label} 包裹
  - 公式外的任何文字 → 不改动

用法：
  python md_typora_fix.py <目录或文件> [--dry-run]
"""

import os, re, sys

def fix_math_content(inner):
    """Wrap Chinese and English word-labels inside math content."""
    result = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        # Chinese / full-width chars → wrap
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            j = i
            while j < len(inner) and (
                '\u4e00' <= inner[j] <= '\u9fff' or
                '\u3000' <= inner[j] <= '\u303f' or
                '\uff00' <= inner[j] <= '\uffef'
            ):
                j += 1
            result.append('\\text{' + inner[i:j] + '}')
            i = j
            continue

        # English word (3+ consecutive letters) → wrap as \text{word}
        # Only when preceded by _ { or space (subscript/superscript context)
        if ch.isalpha() and ch.isascii():
            j = i
            while j < len(inner) and inner[j].isalpha() and inner[j].isascii():
                j += 1
            word_len = j - i
            if word_len >= 3:
                # Check context: preceded by _ { , space or at start
                prev_char = inner[i-1] if i > 0 else ' '
                if prev_char in '_{, =\n':
                    result.append('\\text{' + inner[i:j] + '}')
                    i = j
                    continue
            result.append(ch)
            i += 1
            continue

        result.append(ch)
        i += 1
    return ''.join(result)


def fix_file(fpath, dry_run=False):
    """Fix a single MD file."""
    with open(fpath, 'r', encoding='utf-8') as fh:
        c = fh.read()
    orig = c

    # Step 1: Strip ALL existing \text{} first (clean slate)
    c = re.sub(r'\\text\{([^}]*)\}', r'\1', c)

    # Step 2: Collect math blocks
    markers = []
    def save(m):
        markers.append(m.group(0))
        return f'<<<M{len(markers)-1}>>>'

    c = re.sub(r'\$\$(.+?)\$\$', save, c, flags=re.DOTALL)
    c = re.sub(r'\$([^$]+?)\$', save, c)

    # Step 3: Fix each math block
    for i, block in enumerate(markers):
        if block.startswith('$$'):
            inner = block[2:-2]
            delim = '$$'
        else:
            inner = block[1:-1]
            delim = '$'
        markers[i] = delim + fix_math_content(inner) + delim

    # Step 4: Restore
    for i, block in enumerate(markers):
        c = c.replace(f'<<<M{i}>>>', block)

    if c != orig:
        if not dry_run:
            with open(fpath, 'w', encoding='utf-8') as fh:
                fh.write(c)
        return True
    return False


def fix_all(target, dry_run=False):
    """Fix all .md files under target directory."""
    all_md = []
    if os.path.isfile(target):
        all_md = [target]
    else:
        for dirpath, _, filenames in os.walk(target):
            for f in filenames:
                if f.endswith('.md'):
                    all_md.append(os.path.join(dirpath, f))

    mode = '[DRY-RUN]' if dry_run else '[FIX]'
    print(f'{mode} Scanning {len(all_md)} MD files...\n')
    fixed = 0
    for fpath in all_md:
        if fix_file(fpath, dry_run=dry_run):
            fixed += 1
            print(f'  {mode} {os.path.basename(fpath)}')
    print(f'\nDone. {fixed} files {"would be" if dry_run else ""} fixed.')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Fix MD math for Typora compatibility')
    p.add_argument('target', help='Directory or file to fix')
    p.add_argument('--dry-run', action='store_true', help='Preview only')
    args = p.parse_args()
    fix_all(args.target, dry_run=args.dry_run)
