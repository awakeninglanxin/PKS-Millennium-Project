#!/usr/bin/env python3
"""
CalcPlot3D URL Generator v2 — 支持全部 6 种 3D 可视化对象。

支持类型:
  implicit    隐式曲面    "x^2+y^2+z^2=1-z^3"
  function    函数曲面    "z = sin(x)*cos(y)"
  spacecurve  空间曲线    "x=cos(3t);y=sin(2t);z=0"
  parametric  参数曲面    "x=cos(u)sinh(v);y=sin(u)cosh(v);z=v"
  vectorfield 向量场      "m=x-4y;n=5x+y;p=0"
  revolution  旋转体      "f(x)=x^2; a=0; b=2; axis=y"

用法 (命令行):
    python generate.py implicit "x^2+y^2+z^2=1-z^3" --color "rgb(255,80,80)" --open
    python generate.py function "z=sin(x)*cos(y)" --umin -3 --umax 3 --vmin -3 --vmax 3 --open
    python generate.py spacecurve "x=cos(3t);y=sin(2t);z=0" --tmin 0 --tmax 6.283 --open
    python generate.py parametric "x=cos(u)sinh(v);y=sin(u)cosh(v);z=v" --open
    python generate.py vectorfield "m=x-4y;n=5x+y;p=0" --open
    python generate.py revolution "f(x)=x^2; a=0; b=2" --open

公开地址:
    github.com/awakeninglanxin/PKS-Millennium-Project/tree/main/工具库/calcplot3d-url-gen
"""

import re
import sys
import math
import webbrowser
import urllib.parse

# ============================================================
# 0. 公共工具
# ============================================================
WINDOW_TEMPLATE = (
    "type=window;"
    "showfunnot=false;hsrmode=3;nomidpts=true;anaglyph=-1;"
    "center=8.24,4.76,3.09,1;focus=0,0,0,1;up=0,0,2,1;"
    "transparent=false;alpha=140;twoviews=false;unlinkviews=false;"
    "axisextension=0.7;"
    "xaxislabel=x;yaxislabel=y;zaxislabel=z;"
    "edgeson=true;faceson=true;showbox=true;showaxes=true;showticks=true;"
    "perspective=true;centerxpercent=0.5;centerypercent=0.5;"
    "rotationsteps=30;autospin=true;"
    "xygrid=false;yzgrid=false;xzgrid=false;gridsonbox=false;gridplanes=false;"
    "gridcolor=rgb(128,128,128);"
    "lastaddedsurfaceactive=false;disabletrace=false;activefun=-1;"
)

# ============================================================
# -1. 自动类型识别
# ============================================================
def detect_type(equation):
    """
    根据方程字符串特征自动判断 CalcPlot3D 对象类型。
    返回: (type_str, 提取的域参数 or None)
    """
    s = equation.strip()

    # --- 3D 点: (x,y,z) 括号形式 ---
    if re.match(r'^\([\d\s,.+\-]+\)$', s):
        return 'point', None

    # --- 3D 向量: <x,y,z> 尖括号形式 ---
    if re.match(r'^<[\d\s,.+\-]+>$', s):
        return 'vector', None

    # --- 向量场: 含 m=...; n=...; p=... 模式 ---
    if re.search(r'\bm\s*=', s) and re.search(r'\bn\s*=', s):
        return 'vectorfield', None

    # --- 旋转体: 含 f(x)= 或 f(y)= 模式, 且没有 z= ---
    if (re.search(r'\bf\(x\)\s*=', s) or re.search(r'\bf\(y\)\s*=', s)) and not re.search(r'\bz\s*=', s):
        # 提取 a= 和 b= 作为域边界
        dom = {}
        m = re.search(r'\ba\s*=\s*([-\d.]+)', s)
        if m: dom['a'] = float(m.group(1))
        m = re.search(r'\bb\s*=\s*([-\d.]+)', s)
        if m: dom['b'] = float(m.group(1))
        return 'revolution', dom or None

    # --- 参数曲面: 含 u 和 v 变量 + 多个 x= y= z= ---
    if_uv = bool(re.search(r'\b[uv]\b', s))
    has_xyz_params = (re.search(r'\bx\s*=', s) and re.search(r'\by\s*=', s))
    if if_uv and has_xyz_params and not re.search(r'\bt\b', s):
        return 'parametric', None

    # --- 空间曲线: 含 t 变量 + x= y= z= 模式, 且 t 不是函数名 / 没有 u,v ---
    has_t = bool(re.search(r'(?<![a-z])t(?![a-z])', s))  # t 独立出现(允许 3t, sin(t) 等)
    if has_t and has_xyz_params and not if_uv:
        # 排除 f(t)= 这种函数定义 / 排除含 u,v 的参数曲面
        if not re.search(r'\bf\(t\)', s) and 'sinh' not in s:
            return 'spacecurve', None

    # --- 函数曲面: 以 z= 开头, 右侧只有 x,y (无 z= 等式) ---
    if re.match(r'^z\s*=', s):
        # 确认右侧没有另一个 = 号
        rhs = re.sub(r'^z\s*=\s*', '', s).strip()
        # 排除含 z^2= 或 z= 这种隐式方程误判
        if '=' not in rhs:
            return 'function', None

    # --- 隐式曲面: 含一个 = (且不是 z= 开头) ---
    if '=' in s or '~' in s:
        return 'implicit', None

    # fallback
    return 'implicit', None


def make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom=0.98, scale=1):
    return (
        WINDOW_TEMPLATE +
        f"xmin={xmin};xmax={xmax};"
        f"ymin={ymin};ymax={ymax};"
        f"zmin={zmin};zmax={zmax};"
        f"xscale={scale};yscale={scale};zscale={scale};"
        f"zcmin={zmin*2};zcmax={zmax*2};"
        f"xscalefactor=1;yscalefactor=1;zscalefactor=1;"
        f"tracemode=0;keep2d=true;zoom={zoom}"
    )

def detect_params(text):
    params = set()
    reserved = {'x','y','z','r','t','e','i','u','v','m','n','p','pi','f','g'}
    for m in re.finditer(r'\b([a-d])\b', text):
        p = m.group(1)
        if p not in reserved and p in 'abcd':
            params.add(p)
    return sorted(params)

def encode(text):
    text = text.replace('^', '%5E')
    text = text.replace(' ', '%20')
    return text

def make_slider(name, val=1, pmin=0, pmax=3):
    return (
        f"type=slider;slider={name};value={val};steps=100;"
        f"pmin={pmin};pmax={pmax};"
        f"repeat=true;bounce=true;waittime=1;"
        f"careful=false;noanimate=false;name={name}"
    )


# ============================================================
# 1. 隐式曲面 (implicit) — 已有，微调参数表
# ============================================================
def implicit_url(equation, cubes=60, color="rgb(255,0,0)",
                 xmin=-3.2, xmax=3.2, ymin=-3.2, ymax=3.2,
                 zmin=-3.2, zmax=3.2, zoom=0.98,
                 sliders=None, open_browser=False):
    lhs, rhs = equation.replace('~','=').split('=', 1)
    eq = encode(f"{lhs.strip()}~{rhs.strip()}")
    if sliders is None:
        sliders = {p: (1, 0, 3) for p in detect_params(lhs+rhs)}

    parts = [
        f"type=implicit;equation={eq};cubes={cubes};visible=true;"
        f"fixdomain=true;xmin={xmin};xmax={xmax};ymin={ymin};ymax={ymax};"
        f"zmin={zmin};zmax={zmax};"
        f"alpha=-1;revorient=false;showvf=false;shownormals=false;"
        f"hidemyedges=false;view=0;format=normal;constcol={color}"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 2. 函数曲面 (function / type=z)
# ============================================================
def function_url(z_expr, funname="f",
                 umin=-3, umax=3, vmin=-3, vmax=3, grid=31,
                 color="rgb(232,225,189)", format="normal",
                 contour=False, fixdomain=True,
                 xmin=None, xmax=None, ymin=None, ymax=None,
                 zmin=-2, zmax=2, zoom=0.98,
                 sliders=None, open_browser=False):
    """z_expr: 'sin(x)*cos(y)' 或 'z = sin(x)*cos(y)'"""
    z_expr = re.sub(r'^z\s*=\s*', '', z_expr.strip())
    zeq = encode(z_expr)
    if sliders is None:
        sliders = {p: (1, 0, 3) for p in detect_params(z_expr)}

    if xmin is None: xmin = umin
    if xmax is None: xmax = umax
    if ymin is None: ymin = vmin
    if ymax is None: ymax = vmax

    parts = [
        f"type=z;z={zeq};funname={funname};visible=true;"
        f"umin={umin};umax={umax};vmin={vmin};vmax={vmax};"
        f"grid={grid};format={format};alpha=-1;revorient=false;"
        f"shownormals=false;showvf=false;hidemyedges=false;"
        f"constcol={color};view=0;"
        f"contourcolor=red;fixdomain={'true' if fixdomain else 'false'};activetrace=false;"
        f"contourplot={'true' if contour else 'false'};showcontourplot=false;"
        f"firstvalue=-1;stepsize=0.2;numlevels=11;xnum=46;ynum=46;"
        f"show2d=false;hidesurface=false;hidelabels=true;showprojections=false;"
        f"surfacecontours=true;projectioncolor=rgba(255,0,0,1);"
        f"showxygrid=false;showxygridonbox=false;showconstraint=false"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 3. 空间曲线 (spacecurve)
# ============================================================
def spacecurve_url(params, tmin=0, tmax="2pi", tsteps=100,
                   color="rgb(255,0,0)", width=2,
                   xmin=-2, xmax=2, ymin=-2, ymax=2,
                   zmin=-2, zmax=2, zoom=0.98,
                   sliders=None, open_browser=False):
    """params: 字典 {变量: 表达式} 或 字符串 "x=cos(3t);y=sin(2t);z=0" """
    if isinstance(params, str):
        d = {}
        for part in params.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                d[k.strip()] = v.strip()
        params = d

    x_expr = encode(params.get('x', 't'))
    y_expr = encode(params.get('y', 't'))
    z_expr = encode(params.get('z', '0'))
    all_expr = x_expr + y_expr + z_expr
    if sliders is None:
        sliders = {p: (1, 0, 3) for p in detect_params(all_expr)}

    parts = [
        f"type=spacecurve;spacecurve=curve;curvename=C;"
        f"x={x_expr};y={y_expr};z={z_expr};"
        f"visible=true;width={width};view=0;"
        f"tmin={tmin};tmax={tmax};tsteps={tsteps};"
        f"color={color};showtrace=false;tval=0;constcol=true;twod=false;"
        f"arrows=0;showpt=true;traceptsize=4;trace=true;vel=true;acc=true;"
        f"accnorm=false;acctang=false;veceqs=false;osc=false;k=false;"
        f"showtorsion=false;repeat=false;bounce=false;dashed=false;"
        f"tanline=false;dropcurtain=false;vecwidth=2;numvfpts=10;unitvecscale=1;"
        f"showtvector=false;shownvector=false;showbvector=false;"
        f"showtnbeqs=false;showtnblabels=false;"
        f"showoscplane=false;showrectplane=false;shownormplane=false;"
        f"optimizecurve=true;maxjointangle=10"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 4. 参数曲面 (parametric)
# ============================================================
def parametric_url(params, umin=0, umax="2pi", usteps=40,
                   vmin=-1, vmax=1, vsteps=40,
                   color="rgb(255,0,0)", format="normal",
                   xmin=-2, xmax=2, ymin=-2, ymax=2,
                   zmin=-2, zmax=2, zoom=0.98,
                   sliders=None, open_browser=False):
    """params: "x=cos(u)sinh(v);y=sin(u)cosh(v);z=v" 或 字典"""
    if isinstance(params, str):
        d = {}
        for part in params.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                d[k.strip()] = v.strip()
        params = d

    x_expr = encode(params.get('x', 'u'))
    y_expr = encode(params.get('y', 'v'))
    z_expr = encode(params.get('z', '0'))
    all_expr = x_expr + y_expr + z_expr
    if sliders is None:
        sliders = {p: (1, 0, 3) for p in detect_params(all_expr)}

    parts = [
        f"type=parametric;parametric=2;"
        f"x={x_expr};y={y_expr};z={z_expr};"
        f"visible=true;"
        f"umin={umin};umax={umax};usteps={usteps};"
        f"vmin={vmin};vmax={vmax};vsteps={vsteps};"
        f"alpha=-1;revorient=false;shownormals=false;"
        f"numnormals=10;normalscale=0.5;normalwidth=1;"
        f"showvf=false;hidemyedges=false;view=0;"
        f"format={format};constcol={color};activetrace=false"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 5. 向量场 (vectorfield)
# ============================================================
def vectorfield_url(m, n, p="0",
                    scale=4, nx=9, ny=9, nz=1,
                    twod=True, color="rgb(0,0,255)",
                    xmin=0, xmax=10, ymin=0, ymax=10,
                    zmin=0, zmax=2, zoom=0.5,
                    sliders=None, open_browser=False):
    """m,n,p: x,y,z 的向量分量表达式。
       也支持: "m=x-4y;n=5x+y;p=0" 格式"""
    if isinstance(m, str) and '=' in m:
        d = {}
        for part in m.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                d[k.strip()] = v.strip()
        m = d.get('m', 'x')
        n = d.get('n', 'y')
        p = d.get('p', '0')

    m_expr = encode(str(m))
    n_expr = encode(str(n))
    p_expr = encode(str(p))
    all_expr = m_expr + n_expr + p_expr
    if sliders is None:
        sliders = {p: (1, 0, 3) for p in detect_params(all_expr)}

    parts = [
        f"type=vectorfield;vectorfield=vf;vfname=F;"
        f"m={m_expr};n={n_expr};p={p_expr};"
        f"visible=true;view=0;scale={scale};"
        f"nx={nx};ny={ny};nz={nz};mode=0;"
        f"twod={'true' if twod else 'false'};"
        f"constcol=true;color={color};norm=true;"
        f"desystem=true;objectmode=0;keepobjects=false;activetrace=false"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(
        make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom)
        .replace("perspective=true", "perspective=false")
        .replace("center=8.24,4.76,3.09,1", "center=0,0,50,1")
        .replace("up=0,0,2,1", "up=0,2,0,1")
    )
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 6. 旋转体 (volrev / Solids of Revolution)
# ============================================================
def revolution_url(top2d, bot2d="0",
                   umin=0, umax=2, axisvar="y", axisval=0,
                   color="rgb(255,0,0)", grid="50,25",
                   xmin=-4, xmax=4, ymin=-4, ymax=4,
                   zmin=-4, zmax=4, zoom=0.5,
                   sliders=None, open_browser=False):
    """top2d: 母线函数 f(x) 或 "f(x)=x^2; a=0; b=2" 格式"""
    if isinstance(top2d, str) and '=' in top2d:
        d = {}
        for part in top2d.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                d[k.strip()] = v.strip()
        top_expr = d.get('f(x)', d.get('top', top2d))
        if 'a' in d: umin = float(d['a'])
        if 'b' in d: umax = float(d['b'])
        if 'axis' in d: axisvar = d['axis']
        bot_expr = d.get('bot', '0')
    else:
        top_expr = str(top2d)
        bot_expr = str(bot2d)

    top_enc = encode(top_expr)
    bot_enc = encode(bot_expr)
    if sliders is None:
        sliders = {p: (1, 0, 3) for p in detect_params(top_expr + bot_expr)}

    parts = [
        f"type=volrev;volrev=x;visible=true;alpha=-1;hidemyedges=false;"
        f"view=0;format=normal;constcol={color};"
        f"top2d={top_enc};bot2d={bot_enc};"
        f"umin={umin};umax={umax};axisvar={axisvar};axisval={axisval};"
        f"revsliderval=0;grid={grid};showreprect=false;"
        f"reprectcolor=rgb(255,0,0);reprectxval=0;reprectrotsliderval=0;"
        f"showwashers=false;nslices=4;hidevrregionxy=false;"
        f"polarform=t;polartop=undefined;polarbottom=undefined;"
        f"polarmin=undefined;polarmax=undefined"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(
        make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom)
        .replace("center=8.24,4.76,3.09,1", "center=5,3,10")
        .replace("up=0,0,2,1", "up=0,2,0")
    )
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 7. 点 (type=point)
# ============================================================
def point_url(pos, color="rgb(0,0,0)", size=4,
              xmin=-2, xmax=2, ymin=-2, ymax=2,
              zmin=-2, zmax=2, zoom=0.98,
              sliders=None, open_browser=False):
    """pos: 坐标元组 (x,y,z) 或 "(1,2,3)" 字符串"""
    if isinstance(pos, str):
        pos = pos.strip("()").split(",")
        pos = tuple(float(p.strip()) for p in pos)
    parts = [
        f"type=point;point=({pos[0]},{pos[1]},{pos[2]});visible=true;"
        f"color={color};size={size}"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 8. 向量 (type=vector)
# ============================================================
def vector_url(direction, initialpt="(0,0,0)", color="rgb(255,0,0)", size=2,
               xmin=-2, xmax=2, ymin=-2, ymax=2,
               zmin=-2, zmax=2, zoom=0.98,
               sliders=None, open_browser=False):
    """direction: "<1,2,1.5>" 或 "(1,2,1.5)", initialpt: 起点坐标"""
    parts = [
        f"type=vector;vector={encode(str(direction))};visible=true;"
        f"color={color};size={size};initialpt={encode(str(initialpt))}"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 9. 文字标注 (type=text)
# ============================================================
def text_url(text, position="(0,0,0)", color="rgb(0,0,0)",
             font="Times New Roman", fontsize="14pt",
             bold=False, italic=False, mathmode=True, align="Center",
             xmin=-2, xmax=2, ymin=-2, ymax=2,
             zmin=-2, zmax=2, zoom=0.98,
             sliders=None, open_browser=False):
    """text: 标注文字(支持MathJax LaTeX), position: 位置坐标"""
    t_enc = encode(text)
    t_enc = t_enc.replace('=', '~')  # text 中 = 也要用 ~ 替代
    f_enc = encode(font)
    parts = [
        f"type=text;text={t_enc};visible=true;"
        f"point={encode(str(position))};color={color};"
        f"font={f_enc};fontsize={fontsize};"
        f"bold={'true' if bold else 'false'};"
        f"italic={'true' if italic else 'false'};"
        f"fontmath={'true' if mathmode else 'false'};"
        f"align={encode(align)}"
    ]
    if sliders:
        for n, (v, lo, hi) in sliders.items():
            parts.append(make_slider(n, v, lo, hi))
    parts.append(make_window(xmin, xmax, ymin, ymax, zmin, zmax, zoom))
    url = "https://c3d.libretexts.org/CalcPlot3D/index.html?" + "&".join(parts)
    if open_browser:
        webbrowser.open(url)
    return url


# ============================================================
# 10. CLI — 统一入口
# ============================================================
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="CalcPlot3D URL Generator v2 — 6种3D对象全支持 + 自动识别",
        epilog="示例: python generate.py 'x^2+y^2+z^2=1-z^3' --open  (类型自动识别)")
    ap.add_argument("equation", help="方程")
    ap.add_argument("--type", default="auto",
                    choices=["auto","implicit","function","spacecurve",
                    "parametric","vectorfield","revolution","point","vector","text"],
                    help="对象类型 (默认 auto=自动识别)")
    ap.add_argument("--color", default="rgb(255,0,0)", help="颜色")
    ap.add_argument("--open", action="store_true", help="自动打开浏览器")
    ap.add_argument("--umin", type=float, default=None)
    ap.add_argument("--umax", type=float, default=None)
    ap.add_argument("--vmin", type=float, default=None)
    ap.add_argument("--vmax", type=float, default=None)
    ap.add_argument("--tmin", type=float, default=None)
    ap.add_argument("--tmax", default=None)
    ap.add_argument("--slider", action="append", default=None,
                    help="name=val:min:max")
    ap.add_argument("--cubes", type=int, default=60)
    ap.add_argument("--grid", type=int, default=31)
    ap.add_argument("--zoom", type=float, default=0.98)

    args = ap.parse_args()

    sliders = {}
    if args.slider:
        for s in args.slider:
            n, rest = s.split('=')
            v, lo, hi = rest.split(':')
            sliders[n] = (float(v), float(lo), float(hi))

    extra = dict(sliders=sliders or None, open_browser=args.open,
                 color=args.color)

    # 自动识别类型
    obj_type = args.type
    auto_dom = None
    if obj_type == "auto":
        obj_type, auto_dom = detect_type(args.equation)
        print(f"[auto] 识别为: {obj_type}", file=sys.stderr)

    # 应用自动域
    if auto_dom and obj_type == "revolution":
        if args.umin is None and 'a' in auto_dom:
            args.umin = auto_dom['a']
        if args.umax is None and 'b' in auto_dom:
            args.umax = auto_dom['b']

    if obj_type == "implicit":
        extra["cubes"] = args.cubes
        url = implicit_url(args.equation, **extra)
    elif obj_type == "function":
        if args.umin is not None: extra["umin"] = args.umin
        if args.umax is not None: extra["umax"] = args.umax
        if args.vmin is not None: extra["vmin"] = args.vmin
        if args.vmax is not None: extra["vmax"] = args.vmax
        extra["grid"] = args.grid
        url = function_url(args.equation, **extra)
    elif obj_type == "spacecurve":
        if args.tmin is not None: extra["tmin"] = args.tmin
        if args.tmax is not None: extra["tmax"] = args.tmax
        url = spacecurve_url(args.equation, **extra)
    elif obj_type == "parametric":
        if args.umin is not None: extra["umin"] = args.umin
        if args.umax is not None: extra["umax"] = str(args.umax)
        if args.vmin is not None: extra["vmin"] = args.vmin
        if args.vmax is not None: extra["vmax"] = args.vmax
        url = parametric_url(args.equation, **extra)
    elif obj_type == "vectorfield":
        url = vectorfield_url(args.equation, "y", "0", **extra)
    elif obj_type == "revolution":
        if args.umin is not None: extra["umin"] = args.umin
        if args.umax is not None: extra["umax"] = args.umax
        url = revolution_url(args.equation, **extra)
    elif obj_type == "point":
        url = point_url(args.equation, **extra)
    elif obj_type == "vector":
        url = vector_url(args.equation, **extra)
    elif obj_type == "text":
        url = text_url(args.equation, **extra)

    print(url)
