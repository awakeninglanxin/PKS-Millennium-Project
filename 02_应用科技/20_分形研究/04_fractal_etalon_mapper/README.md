# Fractal Etalon Mapper — 七族映射路径完整框架
==============================
将 NLS etalon 频率映射到 Mandelbrot / 逆 Mandelbrot 复平面，
检验是否落在螺旋中心或 bulb 节点上。

## 快速开始

```bash
cd fractal_etalon_mapper
pip install -r requirements.txt

# 七族20条路径全跑
python main_framework.py --mode all --etalon-csv organ_etalon_356.csv --map

# 单条路径测试
python main_framework.py --mode map --map-method G1_bulb_center
```

## 输出

| 文件 | 内容 |
|------|------|
| `04_output/hit_ranking.json` | 20条路径命中率排名 |
| `04_output/all_points.npz` | 所有路径映射点 |
| `04_output/best_*.csv` | 最优路径坐标 |

## 七族路径

| 族 | 条数 | 核心路径 |
|------|:--:|------|
| A 对数/倒数 | 4 | 1/f, log(f) |
| B 复指数/相角 | 3 | 对数螺旋 |
| C 黄金比例 | 2 | φ=1.618 ⭐ |
| D M参数平面 | 3 | Val1→Re, Val2→Im |
| E 双频比率 | 2 | v2/v1 |
| F 分形维数 | 2 | Box-counting |
| G Farey/Bulb | 2 | Douady-Hubbard ⭐⭐ |
