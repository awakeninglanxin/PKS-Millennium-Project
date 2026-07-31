# 逆M分形 DESCRIPTOR 格式标准 — UF1-22算法参数化序列化方案

> 2026-07-13 | 目标: 将任意UF渲染图压缩为~100B参数描述符, 解压时bit-exact还原

---

## 1. 格式定义

```json
{
  "schema": "inverse-m-descriptor/1.0",
  "family": "c_type",
  "projection": {"type": "inversion", "k": 0.0},
  "viewport": [-1.833, 4.5, -2.124, 2.124],
  "resolution": [1800, null],
  "max_iter": 200,
  "bailout": 50,
  "algorithm": "binary_decomposition",
  "algo_params": {"ANGLE_BINS": 512, "ITER_MOD": 2},
  "colormap": "tree_line",
  "rot90": 3
}
```

## 2. 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `schema` | str | 格式版本 | `"inverse-m-descriptor/1.0"` |
| `family` | enum | 迭代函数族 | `c_type` / `lambda_type` |
| `projection` | dict | 平面变换 (Möbius) | `{"type":"inversion","k":0}` |
| `viewport` | [4]float | 视口 [xmin,xmax,ymin,ymax] | 水滴默认: `[-1.833,4.5,-2.124,2.124]` |
| `resolution` | [2]int | 宽×高, null=按比例自动 | `[1800,null]` |
| `max_iter` | int | 最大迭代次数 | 200 |
| `bailout` | float | 逃逸半径 | 50 |
| `algorithm` | enum | 着色算法 (UF名称) | `"binary_decomposition"` |
| `algo_params` | dict | 算法专属参数 | `{"ANGLE_BINS":512}` |
| `colormap` | str/array | 调色板 | `"plasma"` / RGB浮点数组 |
| `rot90` | int | 旋转次数 | 3 (水滴尖朝上) |

## 3. 投影类型枚举

| projection.type | 公式 | k | 说明 |
|------|------|:--:|------|
| `"identity"` | `c = p` | — | 标准M集 |
| `"inversion"` | `c = k + 1/p` | 0 | 标准逆M（水滴） |
| `"inversion"` | `c = k + 1/p` | 0.25 | 心形→抛物线 |
| `"inversion"` | `c = k + 1/p` | −2 | 天线尖端放大 |
| `"inversion"` | `c = k - 1/p` | cf | Feigenbaum点反演 |
| `"exponentiation"` | `c = cf + e^p` | — | 指数映射 |

## 4. 算法枚举 (UF1-22)

| algorithm | UF# | algo_params 关键字段 |
|------|:--:|------|
| `"binary_decomposition"` | 1 | `{"ANGLE_BINS":64,"POT_STEP":0.12}` |
| `"smooth_potential"` | 2 | `{"percentile_low":2,"percentile_high":98}` |
| `"external_rays"` | 3 | `{"RAY_CNT":128,"LTH":0.008}` |
| `"distance_estimator"` | 4 | `{"stroke_threshold":1e-6}` |
| `"orbit_trap"` | 5 | `{"trap_type":"grid"}` |
| `"topological_decomposition"` | 6 | `{"RAY_DIV":64,"POT_STEP":0.06,"K":4}` |
| `"trajectory_trees"` | 7 | `{"STEP":8}` |
| `"dual_triangulation"` | 8 | `{"RAY_DIV":256,"POT_STEP":0.04}` |
| `"lighting"` | 9 | `{"light_dir":[1,1]}` |
| `"emboss"` | 10 | `{}` |
| `"triangle_inequality"` | 11 | `{"version":"v1"}` |
| `"gaussian_integer"` | 12 | `{}` |
| `"basic"` | 13 | `{}` |
| `"decomposition"` | 14 | `{"num_colors":6}` |
| `"direct_orbit_trap"` | 15 | `{"trap_type":"origin"}` |
| `"gradient"` | 16 | `{"hue_shift":0}` |
| `"exponential_smoothing"` | 17 | `{"decay":0.3}` |
| `"multi_trap"` | 18 | `{"trap_shapes":["heart","circle","cross"]}` |
| `"ripple_kaleidoscope"` | 19 | `{"freq_r":5,"freq_theta":8}` |
| `"advanced_tia"` | 20 | `{"weighted":true}` |
| `"chess_dem_hybrid"` | 21 | `{"ANG_DIV":240,"DIST_LOG_STEP":0.035,"DEM_SCALE":15}` |
| `"image_mapping"` | 22 | `{"source_image":"base64..."}` |

## 5. 压缩比实测

| UF算法 | PNG大小 | DESCRIPTOR大小 | 压缩比 |
|:--|:--:|:--:|:--:|
| UF1 二分棋盘格 | ~800KB | ~180B | ~4500:1 |
| UF4 DEM壳线 | ~500KB | ~150B | ~3400:1 |
| UF21 v4c 细格 | ~1.7MB | ~220B | ~7900:1 |
| 20种变换视频 (100帧) | ~50MB GIF | ~800B 参数 | ~64000:1 |
