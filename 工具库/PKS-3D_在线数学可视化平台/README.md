# PKS-3D 在线数学可视化平台

> CalcPlot3D 超集 — 开源 Three.js + math.js 数学可视化网页

## 文件清单

| 文件 | 说明 | 大小 |
|:---|:---|:--|
| `PKS-3D_开源数学可视化平台.html` | 🏆 主平台 — 多对象并发 + dark/light主题 + URL兼容导入 | ~20KB |
| `Mini3D.html` | 🧪 轻量版 — 函数曲面+空间曲线二合一渲染验证 | ~10KB |
| `CalcPlot3D.min.js` | 📦 官方压缩源码 (1MB) — 反向工程原始材料 | 1MB |
| `CalcPlot3D.readable.js` | 📖 解压可读版 (1.3MB, 31875行) — 完整逆向结果 | 1.3MB |

## 使用方法

```bash
# 直接双击 .html 文件在浏览器打开
# 或本地服务器
python -m http.server 8080
# 访问 http://localhost:8080
```

## 特性

- ✅ 9 种 3D 对象支持
- ✅ dark/light 主题一键切换
- ✅ CalcPlot3D URL 兼容导入
- ✅ math.js 安全解析引擎
- ✅ 多对象并发渲染
- ✅ OrbitControls 鼠标交互
- ✅ MIT 开源
