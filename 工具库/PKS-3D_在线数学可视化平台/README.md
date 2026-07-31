# PKS-3D 在线数学可视化平台

> 🌐 开源 Three.js + math.js 数学 3D 可视化 | CalcPlot3D 超集
> 🤖 **与 AI 大模型配合使用** | 自然语言 → 3D 图形

---

## 快速体验

**双击 `PKS-3D_开源数学可视化平台.html`**，浏览器直接打开，零安装。

---

## 🤖 小白教程：用 AI 大模型生成你的 3D 图形

### 核心思路

这个网页的代码是**完全可读、可修改**的单文件 HTML。你把代码复制给 WorkBuddy / Cursor / Claude / ChatGPT，用自然语言描述你想要的图形，AI 帮你改代码，刷新浏览器就能看到新效果。

### 第一步：打开网页，先看看默认效果

双击 `PKS-3D_开源数学可视化平台.html`，你会看到：
- 左侧面板：一个函数曲面 `z = sin(x) * cos(y)` + 一条彩虹空间曲线
- 右侧窗口：3D 场景，可以用鼠标旋转/缩放/平移
- 顶部输入框：可以粘贴 CalcPlot3D 的 URL 导入

### 第二步：告诉 AI 你想画什么

把下面这段话复制给 WorkBuddy 或任何 AI 大模型（替换 `【你的公式】` 和 `【你的想法】`）：

```
我有一个 3D 数学可视化网页的源代码。请帮我修改它：

【你的想法，比如：
- 把默认曲面改成 z = x^2 - y^2（马鞍面）
- 添加一条螺旋线：x = t*cos(t), y = t*sin(t), z = 0.5t
- 把背景改成深色主题】
```

### 第三步：把代码给 AI

将 `PKS-3D_开源数学可视化平台.html` 的**全部代码**复制粘贴给 AI，然后加上你的需求。AI 会帮你找出要改的代码位置并返回修改后的完整文件。

### 第四步：保存刷新

把 AI 返回的代码保存为 `.html` 文件，双击打开——你的新图形就在浏览器里了。

---

## 📋 常见需求 × 修改位置速查

| 你想做的事 | 告诉 AI 的关键词 | 代码里的大概位置 |
|:---|:---|:---|
| 换一个函数曲面 | "把默认的 sin(x)*cos(y) 改成..." | 搜索 `sin(x)*cos(y)` |
| 换一条空间曲线 | "把曲线的参数方程改成..." | 搜索 `cos(2.5*t)` 和 `sin(1.8*t)` |
| 改背景颜色 | "把背景改成白色/深色" | 搜索 `--bg` 和 `scene.background` |
| 加一个按钮 | "在左侧工具栏加一个按钮" | 搜索 `<button class=` |
| 改颜色映射 | "把高度颜色改成红蓝渐变" | 搜索 `heightGradient` 函数 |
| 提升网格密度 | "把默认网格 50 改成 80" | 搜索 `grid:50` |
| 导入 CalcPlot3D 链接 | 直接粘贴到顶部输入框点"导入" | 无需改代码 |
| 加一个隐式曲面 | "添加 Marching Cubes 渲染 F(x,y,z)=0" | 搜索 `buildImplicitSurface` |

---

## 🧩 网页架构简介（让 AI 更懂你）

```
PKS-3D_开源数学可视化平台.html
│
├── <style>               ← 🎨 所有颜色、字体、布局
│   └── :root { ... }     ← 改这里就能换主题色
│
├── <div id="sidebar">    ← 📋 左侧控制面板
│   ├── 对象卡片           ← 每个曲面的参数控件
│   └── 底部工具栏         ← 添加/清空按钮
│
├── <div id="viewport">   ← 🖼 右侧 3D 视口
│
└── <script>              ← 🧠 核心渲染引擎 (Three.js)
    ├── scene / camera    ← 3D 场景初始化
    ├── buildFunctionSurface()  ← 函数曲面生成
    ├── buildSpaceCurve()       ← 空间曲线生成
    ├── buildImplicitSurface()  ← 隐式曲面生成
    ├── buildVectorField()      ← 向量场生成
    ├── heightGradient()        ← 高度颜色映射
    ├── rainbow()               ← 彩虹颜色映射
    └── animate()               ← 60fps 渲染循环
```

---

## 🎓 对话示例

### 示例 1：换一个马鞍面

```
👤 用户：帮我把默认曲面改成马鞍面 z = x² - y²

🤖 AI：好的，找到 `addObject('function')` 附近的默认方程
     把 `eq:'sin(x)*cos(y)'` 改成 `eq:'x^2 - y^2'` 即可。
     [返回修改后完整代码]
```

### 示例 2：改成深色主题

```
👤 用户：改成深色背景，像 VS Code 那样

🤖 AI：找到 CSS 里 `:root` 块的变量，把背景色改成深色，
     同时把 Three.js 的 `scene.background` 也改成深色。
     [返回修改后完整代码]
```

### 示例 3：从 CalcPlot3D 导入

```
👤 用户：我有一个 CalcPlot3D 链接，想在这个平台打开

🤖 AI：直接把 URL 粘贴到顶部输入框，点"导入"按钮即可。
     平台会解析 `type=implicit` / `type=z` 等参数并创建对应对象。
```

---

## 📦 文件说明

| 文件 | 说明 | 大小 |
|:---|:---|:--|
| `PKS-3D_开源数学可视化平台.html` | 🏆 主平台 | ~30KB |
| `CalcPlot3D.min.js` | 📦 官方压缩源码（反向工程参考） | 1MB |
| `CalcPlot3D.readable.js` | 📖 解压可读版（31875行，研究用） | 1.3MB |
| `README.md` | 📄 本文件 | — |

---

## ⚙️ 技术栈

- **Three.js 0.160** (ES import map, CDN)
- **math.js 13.0** (CDN, 安全表达式解析)
- **OrbitControls** (鼠标旋转/平移/缩放)
- 纯 HTML 单文件，零依赖本地安装

---

## 🔗 配套工具

- `calcplot3d-url-gen` — Python CLI，公式自动生成 CalcPlot3D 兼容链接
- 位于同仓库 `工具库/calcplot3d-url-gen/`
