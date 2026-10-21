# -*- coding: utf-8 -*-
"""对 RecursiveExercisesVITori.html 做第一批改动（CRLF 安全）：
  ① 导出 GIF 引擎重写（按当前运动的最小周期，相机固定，体积自适应 <5MB）
  ② 「画到第几级」扩到 L0~L7、默认 L0~L6
  ③ 统一预设默认：级间倍率 1 / 摆幅 180 / 速度 0.5 / zoom 1.1
  ④ 参数卡控件默认值同步
"""
import io
import sys

P = '../分形环套环RecursiveExercisesVITori.html'
raw = open(P, 'rb').read()
s = raw.replace(b'\r\n', b'\n').decode('utf-8')
n0 = len(s)


def rep(old, new, tag):
    global s
    c = s.count(old)
    if c != 1:
        print('!! %-32s 匹配 %d 次' % (tag, c))
        sys.exit(1)
    s = s.replace(old, new)
    print('ok %-32s +%d' % (tag, len(new) - len(old)))


def cut(start_mark, end_mark, new, tag):
    """把 [start_mark, end_mark) 整段换掉（end_mark 本身保留）"""
    global s
    i = s.find(start_mark)
    j = s.find(end_mark) if end_mark else -1
    if i < 0 or j < 0 or j <= i:
        print('!! %-32s 找不到区间 %s / %s' % (tag, i, j))
        sys.exit(1)
    s = s[:i] + new + s[j:]
    print('ok %-32s 段替换' % tag)


# ─────────────────────────── ① GIF 引擎 ───────────────────────────
GIF_NEW = r'''  var GIFCH = '', GIFOUT = null;
  var GIFW = 760, GIGH = 620, GIFF = 24;
  var GIF_MAXB = 4.8 * 1048576;   /* 落盘目标：整张 < 5 MB（留 4% 给 GIF 头与调色板） */

  /* ══ 一个「最小周期」，只推进运动相位，相机钉死 ══════════════════════════
     旧版是让**相机**绕 z 轴扫 yaw −180°→180°。两个毛病：
       ① 那不是页面正在演示的运动 —— 你开的是「逐级公转」，导出来的却是相机绕着看；
       ② yaw 扫一圈 ≠ 一个周期：它假设场景有半圈对称（p 为偶 + 没挂曲线）。
          p=7 时后半圈根本不是前半圈的重复，首尾接不上，循环会跳。
     最小周期怎么定：
       · 整圈公转 + 挂主圆/不挂曲线 + 级间倍率 = 1 ⇒ 相位走 360°/p 时，每个父环上的
         p 个子环恰好互换位置、整棵树与自身逐点重合 ⇒ 只做 360°/p（p=2 → 180°、
         p=3 → 120°、p=7 → 51.43°）；
       · 挂曲线 或 mix≠1 ⇒ 子环不在中轴圆的 p 等分点上，转 360°/p 不重合 ⇒ 360°；
       · 往复档（摆幅 < 180°）⇒ sin 要走满 2π 才是完整一次来回 ⇒ 360°。 */
  function gifCycle() {
    var A = (S.revAmp === undefined ? 180 : S.revAmp);
    if (A < 179.5) return { deg: 360, kind: 'swing' };
    var mix = (S.revMix === undefined ? 1 : S.revMix);
    var sym = (!attachOn() || S.attach === 'ring');
    if (sym && Math.abs(mix - 1) < 1e-9 && S.p >= 2) return { deg: 360 / S.p, kind: 'p' };
    return { deg: 360, kind: 'turn' };
  }

  /* 把**整个周期**上所有相位的投影包围盒求并集，锁成一台固定相机。
     不这么做的话每帧都按自己的包围盒定尺度和中心 ⇒ 图会一缩一缩、还会漂。 */
  function gifCam(W, H, angles) {
    var du = viewDir(), d = du[0], up = du[1];
    var info = sceneInfo(sceneStill());
    var c0 = M3.camOrtho(W, H, M3.add(info.c, M3.mul(d, 1e4)), info.c, up, 1);
    c0.center = info.c;
    var acc = [1e300, -1e300, 1e300, -1e300], k, b;
    for (k = 0; k < angles.length; k++) {
      b = projBounds(buildScene(S.a, S.p, S.g, S.mode, S.q, S.rho, angles[k], S.revMode), c0);
      if (b[0] < acc[0]) acc[0] = b[0];
      if (b[1] > acc[1]) acc[1] = b[1];
      if (b[2] < acc[2]) acc[2] = b[2];
      if (b[3] > acc[3]) acc[3] = b[3];
    }
    return camFromBounds(W, H, c0, acc, d, up, info.R);
  }

  /* 单帧：给定相位 + 固定相机。⚠ 临时关掉 S.rev / S.spin —— segsFor 见到这两个会
     把细分倍率降到 0.62，导出应该按满精细度来。 */
  function gifRender(W, H, ph, cam) {
    var cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    var ctx = cv.getContext('2d');
    ctx.fillStyle = '#0b0912'; ctx.fillRect(0, 0, W, H);
    var wasRev = S.rev, wasSpin = S.spin;
    S.rev = false; S.spin = false;
    var sc = buildScene(S.a, S.p, S.g, S.mode, S.q, S.rho, ph, S.revMode);
    S.rev = wasRev; S.spin = wasSpin;
    paintInto(ctx, W, H, sc, cam, { alpha: 1, wire: false });
    return cv;
  }

  /* 体积自适应：从最大最细的一档往下试，第一张 ≤ 4.8 MB 的就用它。
     只降「帧数 / 分辨率」，周期不变 —— nF 帧均匀铺满一个周期，照样首尾无缝。 */
  var GIF_PLAN = [
    { w: 760, h: 620, n: 24 }, { w: 760, h: 620, n: 16 }, { w: 760, h: 620, n: 12 },
    { w: 620, h: 504, n: 20 }, { w: 620, h: 504, n: 14 }, { w: 620, h: 504, n: 10 },
    { w: 500, h: 408, n: 16 }, { w: 500, h: 408, n: 12 },
    { w: 400, h: 328, n: 12 }
  ];
  function gifFramesOf(W, H, nF, cyc) {
    cyc = cyc || gifCycle();
    var angles = [], i, cam, frames = [];
    for (i = 0; i < nF; i++) angles.push(cyc.deg * Math.PI / 180 * (i / nF));
    cam = gifCam(W, H, angles);
    for (i = 0; i < nF; i++) {
      frames.push(gifRender(W, H, angles[i], cam).getContext('2d').getImageData(0, 0, W, H).data);
    }
    return frames;
  }
  function gifSleep() { return new Promise(function (r) { window.setTimeout(r, 0); }); }
  /* ⚠ 必须 async：blobToBase64 返回 Promise，直接赋值会让 gifChunk 对 Promise 调 .substr 而崩 */
  async function gifPrepOne() {
    var cyc = gifCycle(), note = $('gifNote');
    var plan = GIF_PLAN, i, W, H, nF, frames, blob, meta = null;
    function say(t) { if (note) note.textContent = t; }
    for (i = 0; i < plan.length; i++) {
      W = plan[i].w; H = plan[i].h; nF = plan[i].n;
      say('渲染 ' + nF + ' 帧 · ' + W + '×' + H + ' …');
      await gifSleep();
      frames = gifFramesOf(W, H, nF, cyc);
      say('编码 ' + nF + ' 帧 · ' + W + '×' + H + ' …');
      await gifSleep();
      /* 12.5 fps：24 帧约 1.9 s 走完一个周期，看着顺、又不至于把 GIF 撑爆。
         GIF 是**浓缩演示**，不是按页面那 22.8 s/圈 的慢速度录 —— 那需要 300+ 帧。 */
      blob = encodeGif(frames, W, H, 8);
      meta = {
        name: '分形环套环_a' + S.a + '_p' + S.p + '_g' + S.g + '_' + Math.round(cyc.deg) + 'deg',
        w: W, h: H, frames: nF, bytes: blob.size, delayCs: 8,
        deg: cyc.deg, kind: cyc.kind
      };
      if (blob.size <= GIF_MAXB || i === plan.length - 1) break;
      say('这一档 ' + (blob.size / 1048576).toFixed(2) + ' MB 超了 5 MB，降一档重来…');
      frames = null;
      await gifSleep();
    }
    GIFW = W; GIGH = H; GIFF = nF;
    GIFOUT = blob; GIFCH = await blobToBase64(blob);
    return meta;
  }
  function gifChunk(off, len) { return GIFCH.substr(off, len); }
  function gifClear() { GIFOUT = null; GIFCH = ''; }

  function doGif() {
    var note = $('gifNote');
    var cyc = gifCycle();
    var tag = (cyc.kind === 'p') ? ('最小周期 ' + cyc.deg.toFixed(2) + '° = 360°/p')
            : (cyc.kind === 'swing') ? '往复一个来回 360°'
            : '整圈 360°';
    note.textContent = '相机固定，按「' + tag + '」出图…';
    window.setTimeout(async function () {
      try {
        var meta = await gifPrepOne();
        note.textContent = meta.name + '.gif · ' + meta.frames + ' 帧 · ' + meta.w + '×' + meta.h +
          ' · ' + (meta.bytes / 1048576).toFixed(2) + ' MB · ' + tag;
        download(GIFOUT, meta.name + '.gif');
      } catch (ex) { note.textContent = '导出失败：' + ex.message; }
    }, 30);
  }
  async function doPng() {
'''
cut("  var GIFCH = '', GIFOUT = null;", "  async function doPng() {", GIF_NEW, 'GIF 引擎')

# 按钮 title
rep('title="绕相机轴扫一圈，把主视窗存成一张 GIF（单张 &lt; 5 MB）"',
    'title="按当前运动（公转/往复）自动走**一个最小周期**，相机固定；自动压到 5 MB 以内"',
    'GIF 按钮 title')

# ─────────────────────────── ② 画到第几级 ───────────────────────────
rep('''      <select id="selCurveLv" style="flex:1 1 120px">
        <option value="0">只画 L0（默认）</option>
        <option value="1">L0 + L1</option>
        <option value="2">L0 ~ L2</option>
      </select>''',
    '''      <select id="selCurveLv" style="flex:1 1 120px">
        <option value="0">只画 L0</option>
        <option value="1">L0 ~ L1</option>
        <option value="2">L0 ~ L2</option>
        <option value="3">L0 ~ L3</option>
        <option value="4">L0 ~ L4</option>
        <option value="5">L0 ~ L5</option>
        <option value="6" selected>L0 ~ L6（默认）</option>
        <option value="7">L0 ~ L7</option>
      </select>''', '画到第几级 选项')

rep('<span class="nm" style="font-size:12px;min-width:64px">L1–L6 曲线</span>',
    '<span class="nm" style="font-size:12px;min-width:64px">L1–L7 曲线</span>', 'L1–L7 标签')

# ─────────────────────────── ③ DEF 默认 ───────────────────────────
rep("""    curve: true, nW: 5, kW: 1680, nD: 1, kD: 7, curveLv: 0, surf: 'half',""",
    """    curve: true, nW: 5, kW: 1680, nD: 1, kD: 7, curveLv: 6, surf: 'half',""", 'DEF.curveLv=6')

rep("    rev: false, revMode: 'nest', revSpd: 1, revPh: 0, revMix: 1, revAmp: 10,",
    "    rev: false, revMode: 'nest', revSpd: 0.5, revPh: 0, revMix: 1, revAmp: 180,",
    'DEF.revSpd/revAmp')

rep("    yaw: 90, pit: 0, zom: 1,", "    yaw: 90, pit: 0, zom: 1.1,", 'DEF.zom=1.1')

# ─────────────────────────── ④ 控件 value ───────────────────────────
rep('<input type="range" id="sRevAmp" min="0" max="180" step="1" value="15">',
    '<input type="range" id="sRevAmp" min="0" max="180" step="1" value="180">', 'sRevAmp=180')
rep('<input type="number" id="vRevAmp" min="0" max="180" step="1" value="15">',
    '<input type="number" id="vRevAmp" min="0" max="180" step="1" value="180">', 'vRevAmp=180')
rep('<input type="range" id="sRevSpd" min="0.2" max="3" step="0.1" value="1">',
    '<input type="range" id="sRevSpd" min="0.2" max="3" step="0.1" value="0.5">', 'sRevSpd=0.5')
rep('<input type="range" id="sZom" min="0.4" max="3.2" step="0.02" value="1">',
    '<input type="range" id="sZom" min="0.4" max="3.2" step="0.02" value="1.1">', 'sZom=1.1')
rep('<input type="number" id="vZom" min="0.4" max="3.2" step="0.02" value="1">',
    '<input type="number" id="vZom" min="0.4" max="3.2" step="0.02" value="1.1">', 'vZom=1.1')

# ─────────────────────────── ⑤ applyPreset 统一默认 ───────────────────────────
rep('''  function applyPreset(name) {
    var P = PRES[name]; if (!P) return;
    var k;
    for (k in P) S[k] = P[k];
    if (P.revPh === undefined) S.revPh = 0;      /* 换档从 φ=0 开始，不残留上一档的相位 */
    if (P.revAmp === undefined) S.revAmp = 10;''',
    '''  function applyPreset(name) {
    var P = PRES[name]; if (!P) return;
    var k;
    /* 每一档都先落到同一组「演示默认」上，再叠加预设自己的字段：
       级间倍率 1 · 每级摆幅拉满 180（整圈）· 速度 50% · 缩放 1.1。
       于是「点哪个按钮」看到的运动口径都一致，差别只在结构与挂法。 */
    S.revMix = 1; S.revAmp = 180; S.revSpd = 0.5; S.zom = 1.1;
    for (k in P) S[k] = P[k];
    if (P.revPh === undefined) S.revPh = 0;      /* 换档从 φ=0 开始，不残留上一档的相位 */
    if (P.revAmp === undefined) S.revAmp = 180;''', 'applyPreset 默认')

# ─────────────────────────── ⑥ 暴露 gifCycle / gifRender ───────────────────────────
rep("    gifFramesOf: gifFramesOf, gifPrepOne: gifPrepOne, gifChunk: gifChunk, gifClear: gifClear,",
    "    gifFramesOf: gifFramesOf, gifPrepOne: gifPrepOne, gifChunk: gifChunk, gifClear: gifClear,\n"
    "    gifCycle: gifCycle, gifRender: gifRender, gifCam: gifCam, GIF_MAXB: GIF_MAXB,",
    '暴露 gif 新接口')

out = s.replace('\n', '\r\n').encode('utf-8')
open(P, 'wb').write(out)
print('→ 写出 %d 字节（原 %d，%+d）' % (len(out), n0, len(s) - n0))
