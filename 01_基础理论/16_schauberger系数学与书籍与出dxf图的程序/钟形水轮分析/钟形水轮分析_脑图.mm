<map version="1.0.1">
<!-- 钟形水轮分析脑图 -->
<node TEXT="钟形水轮分析" FOLDED="false" BACKGROUND_COLOR="#0891B2" COLOR="#FFFFFF">
<richcontent TYPE="NOTE"><html><head/><body><p>同向10-15% → 反向~96% | 四项效应协同放大 ×9倍</p></body></html></richcontent>

<node TEXT="01_代码分析" FOLDED="false" BACKGROUND_COLOR="#F59E0B">
<richcontent TYPE="NOTE"><html><head/><body><p>V1→V2→V3迭代 + 螺锥dxf扫掠50+版本</p></body></html></richcontent>
<node TEXT="V1(t_min=0)">
<richcontent TYPE="NOTE">3叶片+恒定截面+z_v=1 — 起点=0</richcontent>
</node>
<node TEXT="V2(t_min=-π/6)⭐">
<richcontent TYPE="NOTE">6叶片+衰减截面+z_v=2 — 预扭+双倍速度+向心收缩</richcontent>
</node>
<node TEXT="V3(最优)">
<richcontent TYPE="NOTE">num_t=90优化 → 曲线已收敛</richcontent>
</node>
<node TEXT="关键参数">
<richcontent TYPE="NOTE">angle=0.588=arctan(2/3) — 3-4-5勾股三角蛋形角</richcontent>
</node>
<node TEXT="螺锥dxf扫掠(50+版本)" FOLDED="true">
<richcontent TYPE="NOTE">2024.11-2025.10跨年迭代: 羚羊角→阴阳t2→旋叶发电机→斜流泵→蛋面→摆线螺旋</richcontent>
</node>
</node>

<node TEXT="02_COP物理学基础" FOLDED="false" BACKGROUND_COLOR="#10B981">
<richcontent TYPE="NOTE"><html><head/><body><p>COP≠热力学效率 | 开口系统可从环境提取能量</p></body></html></richcontent>
<node TEXT="标准物理可解释 ✅">
<node TEXT="1. 特斯拉涡轮效应(80-90%)"/>
<node TEXT="2. Ranque-Hilsch涡管(反向剪切层存在)"/>
<node TEXT="3. Coanda+伯努利(蛋形截面延迟分离)"/>
<node TEXT="4. COP>1=开口系统热泵原理"/>
</node>
<node TEXT="需验证 ❓">
<node TEXT="5. 负摩擦/μ_eff&lt;0"/>
<node TEXT="6. 9倍增益完整能量账目"/>
<node TEXT="7. 独立第三方重现实测"/>
</node>
</node>

<node TEXT="03_效率跃升定量" FOLDED="false" BACKGROUND_COLOR="#8B5CF6">
<richcontent TYPE="NOTE"><html><head/><body><p>四项效应×9.0=从10%到96%</p></body></html></richcontent>
<node TEXT="效应1: 相对速度最大化">
<richcontent TYPE="NOTE">v_rel=v_f+v_r(反向) vs |v_f-v_r|(同向) → ×3.3</richcontent>
</node>
<node TEXT="效应2: 滚动轴承效应">
<richcontent TYPE="NOTE">湍流μ_eff→分子μ → 摩擦×1/100</richcontent>
</node>
<node TEXT="效应3: 顺压梯度附面层">
<richcontent TYPE="NOTE">dP/ds&lt;0 → 层流附着98%(vs逆压分离50%)</richcontent>
</node>
<node TEXT="效应4: 对转尾涡回收">
<richcontent TYPE="NOTE">6叶片级联 → 出口涡量×10^{-11}</richcontent>
</node>
</node>

<node TEXT="04_同向vs反向完整对比" FOLDED="false" BACKGROUND_COLOR="#DC2626">
<richcontent TYPE="NOTE"><html><head/><body><p>全公式推导+8个标准参考文献</p></body></html></richcontent>
<node TEXT="欧拉涡轮方程对比">
<richcontent TYPE="NOTE">同向:W=Ω(ω_f·r1^2-Ω·r2^2) 相减 | 反向:W=|Ω|(ω_f·r1^2+|Ω|·r2^2) 相加</richcontent>
</node>
<node TEXT="边界层机制对比">
<richcontent TYPE="NOTE">同向逆压dp/ds&gt;0 → 分离 | 反向顺压dp/ds&lt;0 → 附着</richcontent>
</node>
<node TEXT="特斯拉vs Schauberger对比">
<richcontent TYPE="NOTE">特斯拉:同向无叶片(80-90%) | Schauberger:反向+蛋形(~96%)</richcontent>
</node>
<node TEXT="8个参考文献">
<richcontent TYPE="NOTE">Tesla1913/Dixon2014/Schlichting2017/Glauert1935/Ranque1933/Coanda1936/Popel1952/Schauberger原文</richcontent>
</node>
</node>

<node TEXT="核心公式链" BACKGROUND_COLOR="#DC2626" COLOR="#FFFFFF">
<richcontent TYPE="NOTE"><html><head/><body><p>xy=1→超双曲锥→蛋形截面→v_rel=v_f+v_r→顺压梯度→层流附着→96%</p></body></html></richcontent>
</node>
</node>
</map>
