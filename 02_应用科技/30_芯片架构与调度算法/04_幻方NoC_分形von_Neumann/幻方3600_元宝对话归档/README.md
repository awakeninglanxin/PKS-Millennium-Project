# 5阶完美幻方 (Pandiagonal) 3600种 — 算法来源与网站归档

> 来源: 蓝馨 & 元宝 AI 对话 (2026-07-20)  
> 链接: https://yb.tencent.com/s/GuMfaT0QHByd (17轮对话)  
> 归档日期: 2026-07-20

---

## 一、幻方网站资源汇总

### 核心网站

| 网站 | URL | 内容 |
|------|-----|------|
| **Budshaw.ca — Order5** | `http://budshaw.ca/Order5.html` | 5阶幻方总入口，含 3600 pan5 计数 |
| **Budshaw.ca — Pandiagonal** | `http://budshaw.ca/Pandiagonal.html` | 5阶泛对角幻方 Method I-V 构造法（核心页面） |
| **Budshaw.ca — Gp5Types** | `http://budshaw.ca/Gp5Types.html` | 5阶幻方按 Group 分类 (1-20 组)，pan5 分散在多个组 |
| **Budshaw.ca — Groups5Center13** | `http://budshaw.ca/Groups5Center13.html` | 中心=13 的 5阶幻方分组编号 (3600细分统计) |
| **Budshaw.ca — Order5Special** | `http://budshaw.ca/Order5Special.html` | 专门生成 3600 pan5 的页面 |

### 镜像与补充网站

| 网站 | URL | 内容 |
|------|-----|------|
| **Grogono — Magic Squares** | `http://www.grogono.com/magic/` | Graeco-Latin square 构造法, 144→36 缩减 |
| **Geocities 镜像 (Oocities)** | `http://www.oocities.org/` (含多个 magic square 子目录) | budshaw 的历史镜像, 部分页面的备选访问 |
| **Magic Squares (N.J. Wildberger)** | `https://www.magic-squares.net/` | 泛对角幻方的 Frénicle 分类 |
| **33 Pandiagonal Magic Squares** | (元宝搜索结果之一) | 5阶 pandiagonal 的 33 个特殊案例 |

### 学术参考

| 论文/书籍 | 作者 | 年份 | 内容 |
|-----------|------|:--:|------|
| *On a curious property of vulgar fractions* | J. Farey | 1816 | Farey 序列原始论文 |
| *Calcul des rouages par approximation* | A. Brocot | 1861 | Stern-Brocot 树用于齿轮比 |
| *Coexistence of cycles of a continuous map* | A.N. Sharkovsky | 1964 | Sharkovsky 序 |
| Margossian cavalière method | — | — | 骑士步构造法 (元宝对话中引用) |

---

## 二、文件清单

```
幻方3600_元宝对话归档/
├── README.md                        ← 本文件
├── generate_all_3600_pan5.py        ← Python 生成器 (可独立运行)
├── pan5_all_squares.json            ← 全部 pandiagonal 幻方 (JSON)
├── pan5_36_essentially_different.json ← Frénicle 去重后的 36 个基本型
├── pan5_16_ultramagic.json          ← 16 个 ultramagic (同时 associative)
└── pan5_sample_10.txt               ← 人类可读样本 (前10个)
```

---

## 三、核心算法公式（从元宝对话提取）

### 母构造法一：骑士步 (Margossian cavalière)

```
(r, c) ← (r+1 mod 5, c+2 mod 5)   从 1 在 (0,0) 开始
```

合法步长 `(dr, dc)` 需满足: dr,dc 与 5 互素, dr≠dc
可选: (1,2)(1,3)(2,1)(2,3)(2,4)(3,1)(3,2)(3,4)(4,1)(4,2)(4,3)

### 母构造法二：双拉丁方叠加

```
A[i][j] = i
B[i][j] = (a*i + b*j) mod 5    (a,b 与 5 互素, a≠b)
M[i][j] = 5*A[i][j] + B[i][j] + 1
```

骑士步 (1,2) 对应 B = i + 2j mod 5。

### 3600 = 36 × 4 × 25 变换链

```
36 essentially different (基本型)
  × 4 (1-3-5-2-4 重排族: 原方/对角换/13524重排/13524+对角)
  = 144 basic pandiagonal
  × 25 (5 行循环 × 5 列循环位移)
  = 3600 total
```

### 关键变换：1-3-5-2-4 重排

```
原行序: 1,2,3,4,5 → 新行序: 1,3,5,2,4
原列序: 1,2,3,4,5 → 新列序: 1,3,5,2,4
```

做完仍保持 pandiagonal 属性（5阶特有，因 5 与 2 互素）。

---

## 四、与 PKS 项目 / NoC 芯片路由的关系

此目录处于 `04_幻方NoC_分形von_Neumann/` 下，因为 3600 pan5 的三个核心思想直接映射到芯片 NoC 路由：

| 幻方属性 | NoC 映射 |
|----------|----------|
| 每行每列每个折断对角和 = 65 | 每个 router 的行/列/对角带宽均衡 |
| 36 × 4 × 25 变换群 | 路由器的对称拓扑配置空间 |
| Latin square 正交叠加 | 多维度独立路由（X/Y/时间片） |
| 1-3-5-2-4 重排仍保 pan | 重排 router 端口不破坏路由完备性 |
| 中心 = 13 (5阶幻方中位数) | 中心 router 的均匀负载 |

---

## 五、运行方法

```bash
cd 幻方3600_元宝对话归档/
python generate_all_3600_pan5.py
```

依赖: Python 3.x + numpy + 标准库 (无需 GPU)。

输出:
- JSON: 3600 个 pan5、36 essentially different、16 ultramagic
- TXT: 前 10 个人类可读样本
