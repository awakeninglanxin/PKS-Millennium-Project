# EEQT Breath Animation — Bug 分析与修复计划

## 核心问题
蓝馨反馈：`eeqt_breath_animation.html` 动画没有任何动态像素点变化。

## 问题诊断

### 问题1：透明度太稀薄（最可能的主因）
```javascript
octx.fillStyle = 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',0.045)';
octx.fillRect(px, py, 1, 1);
```
- 每个点只贡献 4.5% 的颜色
- 60,000 个点如果均匀分布在 540×540 ≈ 290,000 像素上
- 期望每个被击中的像素：约 1 个点 = 4.5% 亮度
- **结果：画面几乎看不见任何东西，只有极微弱的痕迹**

### 问题2：Offscreen Canvas 合成方式错误
```javascript
ctx.drawImage(off, 0, 0);  // 只复制一次，不累积
```
- 每次 `render()` 调用都清空主 canvas，再 drawImage offscreen
- 如果 offscreen 上每个像素最多只被"画"一次（大多数像素 0 次）
- 结果：画面是空的或极其稀疏的随机点

### 问题3：Alpha 累积方式问题
- 使用 `fillRect` + alpha 时，单次写入不能累积
- 要么用多次叠加，要么直接写 ImageData

## 修复方案

### 方案A（推荐）：增加每像素击中新版，叠加渲染
- 每个采样点对目标像素写入**不透明**的颜色（alpha=1）
- 用 **多次叠加**（同一区域画多次）来累积亮度
- 或用 ImageData 但只在必要时写入（高性能）

### 方案B：恢复原版的光子累积渲染
- 原版 `_backup_20260404_1120.html` 的 `render` 函数使用 `ctx.lighter` 合成模式
- `ctx.globalCompositeOperation = 'lighter'` 让颜色自然叠加
- 这是正确的"光子累积"物理模型

### 方案C：加入真随机源
- `math.random()` 是伪随机，相同 epsilon 下重跑轨迹相同
- 真正的量子随机数服务（QRNG）可让每次运行独一无二
- 备选免费 QRNG：
  - `https://qrng.physik.hu-berlin.de/binary` （超时，当前不可用）
  - `https://api.quantumlab.xyz/random` （待测试）

## 修复优先级
1. **P0**：用 `ctx.globalCompositeOperation = 'lighter'` 修复累积渲染（10分钟）
2. **P1**：提高点的数量或叠加次数，确保画面有可见内容（5分钟）
3. **P2**：接入 QRNG，让每次运行真正随机（待服务恢复）
4. **P3**：对比原版几何渲染，提升视觉质量

## 待验证项
- [ ] 修复后：ε=0.5 时应该有丰富的分形结构（可见）
- [ ] 修复后：动画过程中画面应持续变化
- [ ] 修复后：ε→1 时应该退化到少数几个亮斑
