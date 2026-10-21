# -*- coding: utf-8 -*-
"""第二批改动：
  ⑤ 「⭐ 最优七级」→ p=7 · g=7 · a=1 · q=0.40 · ρ=0.080（实测全程不穿），点开自动整圈公转
  ⑥ 间隙账本：q ≥ sin(π/p) 时直接给根因（这才是「⚠ 有环相交」的真病灶）
  ⑦ 「🔬 滑动安全自检」→ 「🔬 全程自检（按当前运动扫全相位）」
"""
import sys

P = '../分形环套环RecursiveExercisesVITori.html'
s = open(P, 'rb').read().replace(b'\r\n', b'\n').decode('utf-8')


def rep(old, new, tag):
    global s
    c = s.count(old)
    if c != 1:
        print('!! %-30s 匹配 %d 次' % (tag, c)); sys.exit(1)
    s = s.replace(old, new)
    print('ok %-30s %+d' % (tag, len(new) - len(old)))


# ── ⑤ 预设 best ────────────────────────────────────────────────
rep("""    best:  { a: 5, p: 2, g: 6, mode: 'self', q: 0.62, rho: 0.140, curve: true, nW: 5, kW: 1680, nD: 1, kD: 7, surf: 'half' },""",
    """    /* ⭐ 最优七级（2026-10-21 换成 p=7 版）：a=1、p=7、g=7。
       ⚠ q 不能照抄 p=2 的 0.62 —— 见下面 p7Note 的硬上限 sin(π/p)：
         p=7 时 sin(π/7)=0.4339，q 超过它子环直径就大于兄弟间距，ρ 压到 0 也糊在一起。
       取 q=0.40（0.92×上限）、ρ=0.080（全对上限 0.08513 的 94%）。
       72 相位（5°）+ 最坏点 0.625° 细化实测：全程最小比值 0.08513 @339.4°，
       绑定对 **L0/L7（隔 7 级）** ⇒ 余 6.4%；整圈、级间倍率 1、摆幅 180 都不穿。 */
    best:  { a: 1, p: 7, g: 7, mode: 'self', q: 0.40, rho: 0.080, curve: true, nW: 5, kW: 1680, nD: 1, kD: 7,
             surf: 'half', attach: 'curve', revMode: 'nest', revMix: 1, revAmp: 180, revSpd: 0.5 },""",
    'PRES.best → p=7/g=7/a=1')

rep("""      <button id="bBest" style="flex:1 1 100%">⭐ 最优七级（p=2 · q=0.62 · ρ=0.140 · 127 环）</button>""",
    """      <button id="bBest" style="flex:1 1 100%"
        title="a=1 · p=7 · g=7 · q=0.40 · ρ=0.080。整圈 360°、级间倍率 1、摆幅拉满 180 的全程实测最小比值 0.08513（绑定对 L0/L7，隔 7 级）⇒ 余 6.4%，全程不穿。点一下自动开始整圈公转。">⭐ 最优七级（p=7 · g=7 · a=1 · q=0.40 · ρ=0.080）</button>""",
    'bBest 文案')

rep("""    <h2>⭐ 一键最优<span class="badge">匀称 · 梯度一致 · 不重叠</span></h2>""",
    """    <h2>⭐ 一键最优<span class="badge">p=7 · g=7 · a=1 · 全程不穿</span></h2>""",
    'cardBest 徽标')

# bestNote / p7Note 整体重写
cut_start = '''    <p class="note" id="bestNote">按下面四条约束解出来的：<br>'''
cut_end = '''    <div class="row" style="margin-top:6px">
      <button class="gg" data-preset="best3">'''
NEW_NOTES = '''    <p class="note" id="bestNote"><b>p=7 · g=7 · a=1 · q=0.40 · ρ=0.080</b>（2026-10-21 实测档）<br>
      ① 每级 <code>sU(L)=a·q^L</code>、管半径 <code>r(L)=ρ·sU(L)</code> ⇒ 比例匀称、梯度一致；<br>
      ② <b>q 的硬上限 <code>sin(π/p)</code></b>：子环直径 <code>2q·sU</code> 要小于兄弟圆心距
      <code>2·sin(π/p)·sU</code> ⇒ <b>p=7 时 q &lt; 0.4339</b>（p=2 时是 1.0 —— 所以 q=0.62 只在 p=2 成立）；<br>
      ③ 全对（含跨层）实测 <code>ρ ≤ 0.08513</code>，绑定对 <b>L0/L7（隔 7 级）</b>；<br>
      ④ 取 ρ=0.080 ⇒ <b class="okc">余 6.4%</b>；<b>整圈 360° · 级间倍率 1 · 摆幅 180</b>
      的全程最小比值 <b>0.08513 @339.4°</b>（72 相位 + 0.625° 细化）。</p>
    <p class="note" id="p7Note"><b>⚠ 为什么以前一直显示「有环相交」（账本 Δ 却全绿）</b><br>
      · <b>父子 Δ 只量相邻两级</b>。它全过只证明「父亲没被儿子捅穿」；隔了几层的环绕回来撞外层，
        必须做<b>全对复核</b>才能定 —— 这一栏上面那条就是这个复核。<br>
      · 但 p=7 配 <b>q=0.62</b> 时，真病灶根本不是跨层，而是 <b>L2 兄弟</b>：
        <code>sin(π/7)=0.4339 &lt; q=0.62</code> ⇒ 子环直径 <code>2q·sU</code> 已经<b>大于</b>兄弟圆心距
        <code>2·sin(π/p)·sU</code> ⇒ <b>ρ 压到 1/137 也没用</b>：实测两只 L2 的管轴最近只差
        <b>0.00039</b>（比值 0.00051），环本身糊在一起。<br>
      · <b>调参口诀</b>：<b>① 先定 p → ② 取 q ≤ 0.92·sin(π/p) → ③ 再取 ρ ≤ 0.92·(全对上限)</b>。
        p=7 的一组合法解就是上面那档（q=0.40、ρ=0.080）。<br>
      · 想更粗就<b>降 q</b>（<code>ρ上限 ≈ sin(π/p)/q − 1</code> 只是挂主圆的口径，挂曲线要实测），
        但 g=7 时深层 <code>q^7</code> 会小到看不见 —— q=0.40 已是「ρ 够大 / 深层还看得见」的折中。<br>
      · 一键落地：点 <b>🔬 全程自检</b>（按当前运动扫全相位），再点 <b>🛡 ρ 逐级降档</b>。</p>
'''
i = s.find(cut_start); j = s.find(cut_end)
if i < 0 or j < 0 or j <= i:
    print('!! bestNote 区间找不到 %s %s' % (i, j)); sys.exit(1)
s = s[:i] + NEW_NOTES + s[j:]
print('ok bestNote/p7Note 重写')

# ── 点击 best 自动整圈公转 ─────────────────────────────────────
rep("""    $('bBest').addEventListener('click', function () { applyPreset('best'); });""",
    """    $('bBest').addEventListener('click', function () {
      applyPreset('best');
      /* 这一档的手感设定就是「开箱即演示」：整圈 360°、只走公转、相机固定不晃 */
      S.rev = true; S.revPh = 0;
      syncRev(); drawMain(); startLoop();
    });""",
    'bBest 自动公转')

# ── ⑥ 账本里给根因 ────────────────────────────────────────────
rep("""        hh.push(bad ? '<b class="badc">⚠ 有环相交</b>'
                    : (cap ? '<b class="okc">✅ 全部不重叠</b>' : '<b>相邻两级已过</b>'));""",
    """        hh.push(bad ? '<b class="badc">⚠ 有环相交</b>'
                    : (cap ? '<b class="okc">✅ 全部不重叠</b>' : '<b>相邻两级已过</b>'));""",
    '锚点（不改）')

rep("""        hh.push('（L0–L' + g + ' 共 ' + (g + 1) + ' 层 · ' + n0 + ' 只环）<br>');""",
    """        hh.push('（L0–L' + g + ' 共 ' + (g + 1) + ' 层 · ' + n0 + ' 只环）<br>');
        /* 诊因：q ≥ sin(π/p) 时，子环直径已经超过兄弟圆心距 ——
           这不是「管子太粗」，ρ 压到 0 也糊在一起。直接写出来，省得去猜。 */
        var qCap = Math.sin(Math.PI / S.p);
        if (S.q >= qCap - 1e-9) {
          hh.push('<b class="badc">根因：q=' + S.q.toFixed(3) + ' ≥ sin(π/p) = ' + qCap.toFixed(4) + '</b> —— ' +
                  '子环直径 2q·sU 已经超过兄弟圆心距 2·sin(π/p)·sU，<b>ρ 压到 0 也分不开</b>' +
                  '（ρ 只改管子胖瘦，改不了环心位置）。把 q 降到 <b>' + (qCap * 0.9).toFixed(3) + '</b> 以下再看。<br>');
        }""",
    '账本根因诊断')

# ── ⑦ 自检按钮改「全程」 ─────────────────────────────────────
rep("""      <button class="gg" id="bSlide" style="flex:1 1 40%">🔬 滑动安全自检</button>""",
    """      <button class="gg" id="bSlide" style="flex:1 1 40%"
        title="按**当前**运动模式（逐级公转 / 整圈 / 往复 / 沿曲线滑动）把相位扫一圈，每个相位都把全部环对量一遍，取跨相位最小值">🔬 全程自检</button>""",
    'bSlide 文案')

rep("""      n.innerHTML = '点上面的 <b>🔬 滑动安全自检</b>：先把 δ 均匀粗扫 N 个相位，' +""",
    """      n.innerHTML = '点上面的 <b>🔬 全程自检</b>：按<b>当前运动</b>（逐级公转 / 整圈 / 往复 / 沿曲线滑动）' +
        '把相位均匀粗扫 N 个，' +""",
    'slPaint 引导文案')

open(P, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('→ 写出 %d 字节' % len(s.encode('utf-8')))
