# -*- coding: utf-8 -*-
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import System
import math

# -----------------------------
# 交互参数
# -----------------------------
doc_tol = sc.doc.ModelAbsoluteTolerance if sc.doc else 0.01
#global_amp=57.8775  #这是默认整体放大系数，可以修改
#down_shift=133.553  #这是考虑到上接圆筒的高度
global_amp=105.134 #这是默认整体放大系数，可以修改
down_shift=0  #这是考虑到上接圆筒的高度
global_amp = rs.GetReal("global_amp (所有曲线统一缩放系数)，默认：", global_amp, 0.0001) or global_amp
num_bands = int(rs.GetInteger("num_bands (整数, 决定高度范围)", 16, 2) or 16)


t_red_min = rs.GetReal("t_red_min (>0)", 0.5, 1e-6) or 0.5
t_red_max = rs.GetReal("t_red_max (>t_red_min)", float(num_bands), t_red_min+1e-6) or float(num_bands)
deg       = int(rs.GetInteger("曲线阶次 degree (建议3)", 3, 2) or 3)
fit_tol   = rs.GetReal("采样逼近公差/重建公差（越小越贴合）", max(doc_tol*0.5, 1e-5)) or max(doc_tol*0.5, 1e-5)

fit_blue  = rs.GetString("是否对蓝色曲线拟合减点? (Y/N)", "Y")
fit_blue  = (str(fit_blue).strip().upper() == "Y")

# 采样上下限（对红线/轴线）
min_pts = 6
max_pts = 32


# 蓝色螺旋参数
t_s_max = 2.0 * num_bands

# -----------------------------
# 常量与基础函数
# -----------------------------
phi = (math.sqrt(5) - 1) / 2
ln_phi = math.log(phi)  # <0

def red_curve_point(t):
    x = 1.0/t
    z = math.log(t)/ln_phi
    return Rhino.Geometry.Point3d(x*global_amp, 0.0, z*global_amp)

def axis_point_from_t(t):
    z = math.log(t)/ln_phi
    return Rhino.Geometry.Point3d(0.0, 0.0, z*global_amp)

def blue_spiral_point(ts, T):
    r = 2.0/ts
    x = -r*math.cos(T/2.0)
    y = -r*math.sin(T/2.0)
    z = (math.log(ts) - math.log(2.0))/ln_phi
    return Rhino.Geometry.Point3d(x*global_amp, y*global_amp, z*global_amp)

def build_interp_curve(points, degree=3):
    if len(points) < degree+1:
        return None
    try:
        crv = Rhino.Geometry.Curve.CreateInterpolatedCurve(
            points, degree, Rhino.Geometry.CurveKnotStyle.NonUniform
        )
        return sc.doc.Objects.AddCurve(crv)
    except:
        return rs.AddInterpCurve(points, degree)  # 兜底

def chebyshev_in_log_space(n, tmin, tmax):
    a = math.log(tmin); b = math.log(tmax)
    pts = []
    for k in range(n):
        xk = math.cos((2.0*k+1)*math.pi/(2.0*n))
        lk = 0.5*(a+b) + 0.5*(b-a)*xk
        pts.append(math.exp(lk))
    pts.sort()
    return pts

def adaptive_log_sampling(tmin, tmax, start_n=6, max_n=64, check_n=200, tol=1e-3):
    n = max(start_n, 4)
    while n <= max_n:
        ts = chebyshev_in_log_space(n, tmin, tmax)
        pts = [red_curve_point(t) for t in ts]
        tmp_id = build_interp_curve(pts, degree=deg)
        if not tmp_id:
            n += 2
            continue
        tmp = rs.coercecurve(tmp_id)
        max_err = 0.0
        for i in range(check_n):
            u = float(i)/(check_n-1)
            tt = tmin * (tmax/tmin)**u
            true_pt = red_curve_point(tt)
            ok, tp = tmp.ClosestPoint(true_pt)
            if not ok:
                max_err = tol*10.0
                break
            on_pt = tmp.PointAt(tp)
            err = true_pt.DistanceTo(on_pt)
            if err > max_err:
                max_err = err
            if max_err > tol:
                break
        rs.DeleteObject(tmp_id)
        if max_err <= tol:
            return ts
        n += max(1, int(0.2*n))
    return chebyshev_in_log_space(max_n, tmin, tmax)

def max_deviation_to_formula(crv_id, tmin, tmax, samples=400):
    """评估红线曲线与解析表达式的最大偏差（用于诊断）"""
    crv = rs.coercecurve(crv_id)
    if not crv: return None
    max_err = 0.0
    for i in range(samples):
        u = float(i)/(samples-1)
        tt = tmin * (tmax/tmin)**u
        true_pt = red_curve_point(tt)
        ok, tp = crv.ClosestPoint(true_pt)
        if not ok: continue
        on_pt = crv.PointAt(tp)
        e = true_pt.DistanceTo(on_pt)
        if e > max_err: max_err = e
    return max_err

def ensure_layer(name, color):
    if not rs.IsLayer(name):
        rs.AddLayer(name, color)
    return name

# -----------------------------
# 1) 生成红线/中轴线（同控制点数）
# -----------------------------
ts_red = adaptive_log_sampling(t_red_min, t_red_max,
                               start_n=min_pts, max_n=max_pts,
                               check_n=200, tol=fit_tol)

red_pts  = [red_curve_point(t)   for t in ts_red]       # ZX 平面：y=0
axis_pts = [axis_point_from_t(t) for t in ts_red]       # ZY 平面：x=0

# 强制落平面（数值更干净）
red_pts  = [Rhino.Geometry.Point3d(p.X, 0.0, p.Z) for p in red_pts]
axis_pts = [Rhino.Geometry.Point3d(0.0, p.Y, p.Z) for p in axis_pts]

red_id  = build_interp_curve(red_pts,  degree=deg)
axis_id = build_interp_curve(axis_pts, degree=deg)

# 上色与入图层
ly_red   = ensure_layer("Funnel_Red_ZX",   System.Drawing.Color.Red)
ly_axis  = ensure_layer("Axis_Purple_ZY",  System.Drawing.Color.Purple)
ly_blue  = ensure_layer("Spiral_Blue_3D",  System.Drawing.Color.Blue)

if red_id:
    rs.ObjectLayer(red_id, ly_red)
    rs.ObjectColor(red_id, System.Drawing.Color.Red)
if axis_id:
    rs.ObjectLayer(axis_id, ly_axis)
    rs.ObjectColor(axis_id, System.Drawing.Color.Purple)

# -----------------------------
# 2) 生成蓝色 3D 螺旋
# -----------------------------
total_points = max(240, int(60 * num_bands))
T_vals = [i * (2.0*math.pi * t_s_max) / float(total_points-1) for i in range(total_points)]
spiral_pts = []
for T in T_vals:
    n_turn = math.floor(T/(2.0*math.pi))
    tau = T - n_turn*(2.0*math.pi)
    ts = n_turn + 1.0 + tau/(2.0*math.pi)
    if ts <= t_s_max:
        spiral_pts.append(blue_spiral_point(ts, T))

blue_id = build_interp_curve(spiral_pts, degree=deg)
if blue_id:
    rs.ObjectLayer(blue_id, ly_blue)
    rs.ObjectColor(blue_id, System.Drawing.Color.Blue)

# -----------------------------
# 3) 仅对蓝色曲线做拟合减点（可选）
#    红线/轴线保持同控制点数，不做单独拟合！
# -----------------------------
if fit_blue and blue_id:
    new_blue = rs.FitCurve(blue_id, degree=deg, distance_tolerance=fit_tol)
    if new_blue: 
        rs.DeleteObject(blue_id)
        blue_id = new_blue
        rs.ObjectLayer(blue_id, ly_blue)
        rs.ObjectColor(blue_id, System.Drawing.Color.Blue)

# 4) 向下平移（整体曲线的高度+down_shift）
# -----------------------------
all_ids = [i for i in [red_id, axis_id, blue_id] if i]
if all_ids:
    z_min = None
    z_max = None
    for gid in all_ids:
        crv = rs.coercecurve(gid)
        bb = crv.GetBoundingBox(True)
        if not bb: 
            continue
        if z_min is None:
            z_min = bb.Min.Z
            z_max = bb.Max.Z
        else:
            z_min = min(z_min, bb.Min.Z)
            z_max = max(z_max, bb.Max.Z)
    if z_min is not None and z_max is not None:
#        height = z_max #代表r=2的位置向下对齐到原0点平面
        height = 0 #代表r=1的位置在原0点平面 （建议蛋咬一口从此处开始）
        if abs(height) > 1e-12:
            # 向下平移 “整体高度”
            rs.MoveObjects(all_ids, [0.0, 0.0, -height-down_shift])
# -----------------------------
# 6) 诊断输出（控制点数量 + 最大偏差）
# -----------------------------
def ctrlpt_count(crv_id):
    crv = rs.coercecurve(crv_id)
    if not crv: return None
    nurbs = crv.ToNurbsCurve()
    return nurbs.Points.Count if nurbs else None

cnt_red  = ctrlpt_count(red_id)
cnt_axis = ctrlpt_count(axis_id)
cnt_blue = ctrlpt_count(blue_id)

dev_red = max_deviation_to_formula(red_id, t_red_min, t_red_max, samples=600) if red_id else None

rs.ZoomExtents(None, True)

print("—— 生成完成 ——")
print("global_amp = %.6f, degree = %d, fit_tol = %.6g" % (global_amp, deg, fit_tol))
if red_id:
    print("红线 ZX 曲线 控制点数:", cnt_red)
if axis_id:
    print("紫色 ZY 轴线 控制点数:", cnt_axis, "（应与红线完全一致）")
if blue_id:
    print("蓝色 3D 螺旋 控制点数:", cnt_blue, "（可能因拟合而减少）")
if dev_red is not None:
    print("红线对解析式最大偏差 ≈ %.6g (模型单位)" % dev_red)
