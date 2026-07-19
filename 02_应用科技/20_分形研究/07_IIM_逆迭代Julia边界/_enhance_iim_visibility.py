#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IIM 渲染结果后处理增强：把黑底上的浅灰线提亮为可见亮线。"""
import os
from pathlib import Path
from PIL import Image
import numpy as np

def enhance_iim_png(src_path, gamma=0.55, brightness=1.3, sat_boost=0.3, out_path=None):
    """对黑底 Julia IIM 图做前景提亮增强，保持背景纯黑。"""
    img = Image.open(src_path).convert('RGB')
    arr = np.array(img, dtype=np.float32) / 255.0

    # 背景掩膜：接近原始 #08081E 深紫黑
    bg_mask = (arr[:, :, 0] < 0.04) & (arr[:, :, 1] < 0.04) & (arr[:, :, 2] < 0.08)
    fg_mask = ~bg_mask

    # 背景设为纯黑
    arr[bg_mask] = 0.0

    # 前景 gamma 提亮 + 亮度增强
    if fg_mask.any():
        fg = arr[fg_mask]
        fg = np.clip((fg ** gamma) * brightness, 0, 1)
        # 稍微提升饱和度/霓虹感：让最亮通道更白，其余通道也增强
        mx = fg.max(axis=1, keepdims=True)
        fg = np.clip(fg + (1.0 - mx) * sat_boost, 0, 1)
        arr[fg_mask] = fg

    out = Image.fromarray((arr * 255).astype(np.uint8))
    if out_path is None:
        stem = Path(src_path).stem
        out_path = str(Path(src_path).with_name(f'{stem}_高对比可见.png'))
    out.save(out_path, optimize=True)
    return out_path


if __name__ == '__main__':
    root = Path(r'D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\IIM')
    files = [
        'IIM_Julia边界_四经典.png',
        'IIM_Julia边界_四经典_v2批量化.png',
        'IIM_Seahorse_Julia_高清.png',
    ]
    for f in files:
        src = root / f
        if not src.exists():
            print(f'跳过（不存在）: {f}')
            continue
        out = enhance_iim_png(str(src))
        print(f'增强完成: {out}')
