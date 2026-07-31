#!/usr/bin/env python3
"""
CalcPlot3D URL Generator — 给定代数曲面公式，自动生成可打开的正确 CalcPlot3D 链接。

用法 (命令行):
    python generate.py "x^2+y^2+z^2=1-z^3"
    python generate.py "ax^2+ay^2+cz^2=1+d*x^2*z^2" --slider a=1:0:3 --slider c=1:0:3 --slider d=0.5:0:3

用法 (Python import):
    from generate import calcplot3d_url
    url = calcplot3d_url("x^2+y^2+z^2=1-z^3", cubes=60, color="rgb(255,0,0)")
"""

import re
import sys
import math
import webbrowser
import urllib.parse

# ============================================================
# 1. 方程解析
# ============================================================
def parse_equation(eq_str):
    """将用户输入的方程拆成 LHS 和 RHS."""
    eq_str = eq_str.strip()
    # 支持 = 或 ~ 作为等号
    if '~' in eq_str:
        lhs, rhs = eq_str.split('~', 1)
    elif '=' in eq_str:
        lhs, rhs = eq_str.split('=', 1)
    else:
        raise ValueError(f"方程缺少 '=' 或 '~': {eq_str}")
    return lhs.strip(), rhs.strip()


def detect_parameters(eq_str):
    """检测方程中的参数 (a,b,c,d,t)."""
    params = set()
    # 匹配单个字母 a/b/c/d/t，且不是 x/y/z/r/θ/ρ/ϕ/e/pi
    reserved = {'x','y','z','r','t','e','i','π','pi'}
    for m in re.finditer(r'\b([a-d])\b', eq_str):
        p = m.group(1)
        if p not in reserved and p in 'abcd':
            params.add(p)
    return sorted(params)


# ============================================================
# 2. 域范围推断
# ============================================================
def estimate_domain(lhs, rhs):
    """
    基于 RHS 的结构推断可视域。
    
    规则:
    - 若 RHS 为常数 C → x,y,z ∈ [-√|C|, √|C|]
    - 若 RHS 含 z³ 项 → z ∈ [-1.5, 2]
    - 若 RHS 含 e^z / b^z → z ∈ [-2, 2]
    - 否则默认 [-2, 2]
    """
    x_range = [-2.0, 2.0]
    y_range = [-2.0, 2.0]
    z_range = [-2.0, 2.0]
    
    # 尝试取常数
    rhs_clean = rhs.strip()
    const_match = re.match(r'^[+-]?[\d.]+$', rhs_clean)
    if const_match:
        c = abs(float(rhs_clean))
        r = math.sqrt(max(c, 1))
        x_range = [-r * 1.2, r * 1.2]
        y_range = [-r * 1.2, r * 1.2]
        z_range = [-r * 1.2, r * 1.2]
        return x_range, y_range, z_range
    
    # 含 z 的结构 → 调大 z 范围
    if re.search(r'z\^?\d', rhs):
        # z³ → 不对称范围
        if re.search(r'z\^3|z\*\*3|z\*z\*z', rhs) or 'z^3' in rhs:
            z_range = [-1.5, 2.0]
        # z² → 对称
        elif re.search(r'z\^2|z\*\*2|z\*z', rhs) or 'z^2' in rhs:
            z_range = [-2.0, 2.0]
        else:
            z_range = [-2.0, 2.0]
    
    # 含指数项 → 调小范围
    if re.search(r'\be\^|exp\(|b\^z|2\^z', rhs):
        z_range = [-1.5, 1.5]
    
    # 含参数（a,b,c,d）→ 放宽
    if re.search(r'\b[abcd]\b', lhs + rhs):
        x_range = [-3.0, 3.0]
        y_range = [-3.0, 3.0]
        z_range = [min(z_range[0], -2), max(z_range[1], 2)]
    
    return x_range, y_range, z_range


def scale_factor(domain):
    """根据域范围计算合适的 scale."""
    span = domain[1] - domain[0]
    if span <= 2: return 1.0
    if span <= 4: return 0.5
    if span <= 8: return 0.25
    return 0.1


# ============================================================
# 3. URL 编码
# ============================================================
def encode_eq(lhs, rhs):
    """将 LHS~RHS 编码为 URL 安全格式."""
    raw = f"{lhs}~{rhs}"
    # 替换 ^ 为 %5E
    raw = raw.replace('^', '%5E')
    # 替换空格为 %20
    raw = raw.replace(' ', '%20')
    # 确保 * 号保留
    return raw


# ============================================================
# 4. 生成完整 URL
# ============================================================
def calcplot3d_url(
    equation,
    cubes=60,
    color="rgb(255,0,0)",
    x_range=None,
    y_range=None,
    z_range=None,
    sliders=None,
    auto_domain=True,
    open_browser=False
):
    """
    生成 CalcPlot3D 隐式曲面链接。
    
    参数:
        equation: 代数方程，如 "x^2+y^2+z^2=1-z^3"
        cubes: Marching cubes 分辨率 (默认 60)
        color: 曲面颜色 (默认 "rgb(255,0,0)")
        x_range, y_range, z_range: 手动指定域范围 (覆盖自动推断)
        sliders: 滑块定义字典 {参数名: (value, pmin, pmax), ...}
        auto_domain: 是否自动推断域 (默认 True)
        open_browser: 是否自动打开浏览器 (默认 False)
    """
    lhs, rhs = parse_equation(equation)
    eq_encoded = encode_eq(lhs, rhs)
    
    # 自动域推断
    if auto_domain and (x_range is None or y_range is None or z_range is None):
        x_auto, y_auto, z_auto = estimate_domain(lhs, rhs)
        if x_range is None: x_range = x_auto
        if y_range is None: y_range = y_auto
        if z_range is None: z_range = z_auto
    
    x_range = x_range or [-2, 2]
    y_range = y_range or [-2, 2]
    z_range = z_range or [-2, 2]
    
    # Scale
    xsc = scale_factor(x_range)
    ysc = scale_factor(y_range)
    zsc = scale_factor(z_range)
    
    # 自动检测参数
    if sliders is None:
        params = detect_parameters(equation)
        if params:
            sliders = {p: (1, 0, 3) for p in params}
    
    # --- 构建 URL ---
    base = "https://c3d.libretexts.org/CalcPlot3D/index.html?"
    
    # Implicit surface
    implicit = (
        f"type=implicit;"
        f"equation={eq_encoded};"
        f"cubes={cubes};"
        f"visible=true;"
        f"fixdomain=true;"
        f"xmin=-pi;xmax=pi;ymin=-pi;ymax=pi;zmin=-pi;zmax=pi;"
        f"alpha=-1;revorient=false;showvf=false;shownormals=false;"
        f"hidemyedges=false;view=0;format=normal;"
        f"constcol={color}"
    )
    
    parts = [implicit]
    
    # Sliders
    if sliders:
        for name, (val, pmin, pmax) in sliders.items():
            s = (
                f"type=slider;"
                f"slider={name};"
                f"value={val};"
                f"steps=100;"
                f"pmin={pmin};pmax={pmax};"
                f"repeat=true;bounce=true;waittime=1;"
                f"careful=false;noanimate=false;"
                f"name={name}"
            )
            parts.append(s)
    
    # Window (使用已授权的相机模板)
    window = (
        f"type=window;"
        f"showfunnot=false;hsrmode=3;nomidpts=true;anaglyph=-1;"
        f"center=0.6,-39.4,6.75,1;focus=0,0,0,1;up=0.03,0.26,0.96,1;"
        f"transparent=false;alpha=140;twoviews=false;unlinkviews=false;"
        f"axisextension=0.7;"
        f"xaxislabel=x;yaxislabel=y;zaxislabel=z;"
        f"edgeson=true;faceson=true;showbox=true;showaxes=true;showticks=true;"
        f"perspective=true;centerxpercent=0.28;centerypercent=0.28;"
        f"rotationsteps=30;autospin=true;"
        f"xygrid=false;yzgrid=false;xzgrid=false;gridsonbox=false;gridplanes=false;"
        f"gridcolor=rgb(128,128,128);"
        f"lastaddedsurfaceactive=false;disabletrace=false;activefun=-1;"
        f"xmin={x_range[0]};xmax={x_range[1]};"
        f"ymin={y_range[0]};ymax={y_range[1]};"
        f"zmin={z_range[0]};zmax={z_range[1]};"
        f"xscale={xsc};yscale={ysc};zscale={zsc};"
        f"zcmin=-3;zcmax=3;xscalefactor=1;yscalefactor=1;zscalefactor=1;"
        f"tracemode=0;keep2d=true;zoom=1.39"
    )
    parts.append(window)
    
    url = base + "&".join(parts)
    
    if open_browser:
        webbrowser.open(url)
    
    return url


# ============================================================
# 5. CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    
    ap = argparse.ArgumentParser(description="CalcPlot3D URL Generator")
    ap.add_argument("equation", help="代数曲面方程，如 'x^2+y^2+z^2=1-z^3'")
    ap.add_argument("--cubes", type=int, default=60, help="Marching cubes 分辨率")
    ap.add_argument("--color", default="rgb(255,0,0)", help="曲面颜色")
    ap.add_argument("--xmin", type=float, default=None)
    ap.add_argument("--xmax", type=float, default=None)
    ap.add_argument("--ymin", type=float, default=None)
    ap.add_argument("--ymax", type=float, default=None)
    ap.add_argument("--zmin", type=float, default=None)
    ap.add_argument("--zmax", type=float, default=None)
    ap.add_argument("--slider", action="append", default=None,
                    help="滑块定义: name=value:pmin:pmax (可多次使用)")
    ap.add_argument("--open", action="store_true", help="自动打开浏览器")
    ap.add_argument("--no-auto-domain", action="store_true", help="禁用自动域推断")
    
    args = ap.parse_args()
    
    # 解析滑块
    sliders = {}
    if args.slider:
        for spec in args.slider:
            name, rest = spec.split("=")
            val, pmin, pmax = rest.split(":")
            sliders[name] = (float(val), float(pmin), float(pmax))
    
    # 手动域
    x_range = None
    y_range = None
    z_range = None
    if args.xmin is not None and args.xmax is not None:
        x_range = [args.xmin, args.xmax]
    if args.ymin is not None and args.ymax is not None:
        y_range = [args.ymin, args.ymax]
    if args.zmin is not None and args.zmax is not None:
        z_range = [args.zmin, args.zmax]
    
    url = calcplot3d_url(
        args.equation,
        cubes=args.cubes,
        color=args.color,
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        sliders=sliders or None,
        auto_domain=not args.no_auto_domain,
        open_browser=args.open
    )
    
    print(url)
