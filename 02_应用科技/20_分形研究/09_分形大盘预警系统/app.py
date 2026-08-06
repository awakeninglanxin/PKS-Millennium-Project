# -*- coding: utf-8 -*-
"""
app.py — 分形大盘预警系统 · Flask 网页仪表盘 (v1.1 修复+对照版)
================================================================
v1.1 更新:
 1. 修复 ECharts 出框/幽灵调用 bug (lineChart('chart_hurst2') 引用不存在元素
    中断后续 JS; 图表初始化时机在 CSS 布局前导致宽度错误)
 2. 新增【传统大盘预警系统】对照区: 上证指数真实数据 MA/MACD/RSI/BOLL/KDJ
    与分形簇跳率预警并排对比
启动: python app.py  →  http://127.0.0.1:5002
作者: AI · v1.1 2026-08-03
"""

import os
import json
import time
import numpy as np
from flask import Flask, render_template_string, jsonify

from fractal_analysis import (
    build_cjr_timeline, alert_engine, gen_synthetic_panel,
    extract_features, ward_cluster,
)
from traditional_indicators import analyze_traditional

app = Flask(__name__)

# 全局缓存 (1小时)
CACHE = {"ts": 0, "data": None}
CACHE_TTL = 3600

# 通达信模式开关 (接真实行情时改为 "tdx")
TDX_MODE = os.environ.get("TDX_MODE", "sim")

INDUSTRIES = ["半导体", "光模块", "存储", "软件", "医药", "消费", "新能源", "金融"]


# ------------------------------------------------------------
# 通达信数据接入 (placeholder — 接通后实现)
# ------------------------------------------------------------
def fetch_tdx_panel():
    raise NotImplementedError("TDX 接入待配置 — 当前使用模拟数据")


# ------------------------------------------------------------
# 数据准备
# ------------------------------------------------------------
def get_data(force=False):
    now = time.time()
    if CACHE["data"] and not force and now - CACHE["ts"] < CACHE_TTL:
        return CACHE["data"]

    # ---- 分形部分 (模拟面板) ----
    if TDX_MODE == "tdx":
        try:
            panel = fetch_tdx_panel()
        except NotImplementedError:
            panel, _, _, _ = gen_synthetic_panel(n_stocks=40, T=800)
    else:
        panel, codes, crash_days, industries = gen_synthetic_panel(n_stocks=40, T=800)

    tl = build_cjr_timeline(panel, window=120, step=20, cuts=(3, 5, 8))
    tl["cjr"] = {str(k): v for k, v in tl["cjr"].items()}

    codes = list(panel.keys())
    T = min(len(v) for v in panel.values())
    window = 120
    # 锚定聚类末窗口标签 (与簇跳率时序一致)
    labels = tl["last_labels"]
    hursts, widths, hills = tl["avg_hurst"], tl["avg_width"], tl["avg_hill"]

    mid = tl["cjr"]["5"][-1]
    fine = tl["cjr"]["8"][-1]
    alert = alert_engine(mid, fine, hursts[-1], widths[-1])

    cluster_composition = {}
    for k in (3, 5, 8):
        comp = {}
        for i, c in enumerate(codes):
            cl = int(labels[k][i])
            comp.setdefault(cl, []).append(c)
        cluster_composition[str(k)] = comp

    # ---- 传统部分 (真实上证指数) ----
    try:
        trad = analyze_traditional()
        trad_ok = True
    except Exception as e:
        trad = {"alert": {"level": "—", "color": "gray", "msg": f"传统数据获取失败: {e}",
                          "suggestion": "检查网络/API", "signals": []}}
        trad_ok = False

    data = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "tdx_mode": TDX_MODE,
        "n_stocks": len(codes),
        "window": window,
        "timeline": tl,
        "alert": alert,
        "avg_metrics": {
            "hurst": float(hursts[-1]),
            "width": float(widths[-1]),
            "hill": float(hills[-1]),
        },
        "cluster_composition": cluster_composition,
        "current_labels": {str(k): [int(x) for x in labels[k]] for k in (3, 5, 8)},
        "codes": codes,
        "industries": INDUSTRIES,
        "traditional": trad,
        "trad_ok": trad_ok,
    }
    CACHE["ts"] = now
    CACHE["data"] = data
    return data


# ------------------------------------------------------------
# 页面 (v1.1: 修复布局 + 传统对照区)
# ------------------------------------------------------------
PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>分形大盘预警系统 · 与传统大盘预警对照</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Microsoft YaHei',sans-serif; background:#f5f7fa; color:#2c3e50; padding:20px; }
  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:10px; }
  .title { font-size:24px; font-weight:bold; }
  .subtitle { color:#7f8c8d; font-size:13px; margin-top:4px; }
  .alert-banner { display:flex; align-items:center; gap:16px; padding:16px 20px;
    border-radius:10px; margin-bottom:14px; color:#fff; font-size:16px; font-weight:bold; flex-wrap:wrap; }
  .alert-banner .lamp { width:22px; height:22px; border-radius:50%; background:#fff; flex-shrink:0; }
  .alert-banner .tag-r { margin-left:auto; font-weight:normal; font-size:12px; opacity:.9; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  .card { background:#fff; border-radius:10px; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,.06); min-width:0; }
  .card.full { grid-column:1/-1; }
  .card h3 { font-size:15px; margin-bottom:10px; color:#34495e; }
  .chart { width:100%; height:300px; }
  .chart.small { height:220px; }
  .chart.tall { height:340px; }
  .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:18px; }
  .metric { background:#fff; border-radius:10px; padding:14px; text-align:center;
    box-shadow:0 2px 8px rgba(0,0,0,.06); }
  .metric .val { font-size:26px; font-weight:bold; margin-top:4px; }
  .metric .lab { font-size:12px; color:#7f8c8d; }
  .suggestion { background:#eaf2f8; border-left:4px solid #2980b9; padding:12px 16px;
    border-radius:6px; margin-top:14px; font-size:14px; }
  .tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:12px;
    background:#ecf0f1; margin:2px; }
  .signals li { font-size:13px; margin:4px 0; padding:4px 8px; background:#f8f9fa; border-radius:4px; }
  .vs-title { grid-column:1/-1; margin:10px 0 4px; font-size:16px; font-weight:bold;
    color:#1f3864; border-bottom:2px solid #4472C4; padding-bottom:6px; }
  .foot { text-align:center; color:#95a5a6; font-size:11px; margin-top:20px; }
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">分形大盘预警系统 v1.1</div>
    <div class="subtitle">Fractal Structure Alert + 传统指标对照 · 数据: {{ data.date }} · 分形模式: {{ '通达信' if data.tdx_mode=='tdx' else '模拟' }} · 传统: 上证指数真实数据</div>
  </div>
  <button onclick="location.reload()" style="padding:8px 16px;border:none;background:#2980b9;color:#fff;border-radius:6px;cursor:pointer;font-size:14px;">⟳ 刷新</button>
</div>

<div class="alert-banner" style="background:{{ data.alert.color == 'red' and '#e74c3c' or (data.alert.color == 'orange' and '#e67e22' or (data.alert.color == 'gold' and '#f1c40f' or '#27ae60')) }}">
  <div class="lamp" style="box-shadow:0 0 0 4px rgba(255,255,255,.3)"></div>
  <span>【分形预警】{{ data.alert.msg }}</span>
  <span class="tag-r">{{ data.n_stocks }} 只样本 · 窗宽 {{ data.window }} 日</span>
</div>

<div class="metrics">
  <div class="metric"><div class="lab">mid 簇跳率 (k=5)</div><div class="val" style="color:{{ '#e74c3c' if data.timeline.cjr['5'][-1]>0.4 else '#27ae60' }}">{{ '%.1f%%' % (data.timeline.cjr['5'][-1]*100) }}</div></div>
  <div class="metric"><div class="lab">fine 簇跳率 (k=8)</div><div class="val" style="color:{{ '#e74c3c' if data.timeline.cjr['8'][-1]>0.45 else '#27ae60' }}">{{ '%.1f%%' % (data.timeline.cjr['8'][-1]*100) }}</div></div>
  <div class="metric"><div class="lab">平均 Hurst</div><div class="val">{{ '%.3f' % data.avg_metrics.hurst }}</div></div>
  <div class="metric"><div class="lab">分形谱宽 Δh</div><div class="val" style="color:{{ '#e74c3c' if data.avg_metrics.width<0.5 else '#2c3e50' }}">{{ '%.3f' % data.avg_metrics.width }}</div></div>
</div>

<div class="grid">
  <div class="card full"><h3>分形预警 · 簇跳率时序（红色虚线 = 55% 撤退阈值 / 橙色 = 40% 警惕阈值）</h3>
    <div id="chart_cjr" class="chart tall"></div></div>

  <div class="card"><h3>平均 Hurst 指数趋势（&gt;0.5 趋势持续）</h3><div id="chart_hurst" class="chart small"></div></div>
  <div class="card"><h3>多重分形谱宽 Δh 趋势（收窄 = 结构退化）</h3><div id="chart_width" class="chart small"></div></div>

  <div class="card"><h3>分形当前簇构成（mid 切树 k=5）</h3><div id="chart_cluster" class="chart small"></div></div>
  <div class="card"><h3>分形预警 · 操作建议</h3>
    <div class="action-banner" style="background:{{ data.alert.color == 'red' and '#e74c3c' or (data.alert.color == 'orange' and '#e67e22' or (data.alert.color == 'gold' and '#f1c40f' or '#27ae60')) }};color:#fff;padding:10px 14px;border-radius:8px;font-size:15px;font-weight:bold;">
      ▶ {{ data.alert.action }} <span style="font-weight:normal;font-size:12px;opacity:.9">（建议仓位: {{ data.alert.pos }}）</span>
    </div>
    <div class="suggestion">{{ data.alert.suggestion }}</div>
    {% if data.alert.rationale %}
    <div style="margin-top:10px"><b>分析依据</b>
      <ul class="signals">
        {% for r in data.alert.rationale %}
        <li>{{ r }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}
    <div style="margin-top:12px">
      <b>当前窗口指标</b><br>
      <span class="tag">Hurst {{ '%.3f' % data.avg_metrics.hurst }}</span>
      <span class="tag">Δh {{ '%.3f' % data.avg_metrics.width }}</span>
      <span class="tag">Hill α {{ '%.2f' % data.avg_metrics.hill }}</span>
      <span class="tag">mid CJR {{ '%.0f%%' % (data.timeline.cjr['5'][-1]*100) }}</span>
      <span class="tag">fine CJR {{ '%.0f%%' % (data.timeline.cjr['8'][-1]*100) }}</span>
    </div>
  </div>
</div>

<div class="vs-title">▼ 传统大盘预警系统对照（上证指数 · 腾讯行情真实数据）</div>

{% if data.trad_ok %}
<div class="alert-banner" style="background:{{ data.traditional.alert.color == 'red' and '#e74c3c' or (data.traditional.alert.color == 'orange' and '#e67e22' or (data.traditional.alert.color == 'gold' and '#f1c40f' or (data.traditional.alert.color == 'gray' and '#95a5a6' or '#27ae60'))) }}">
  <div class="lamp"></div>
  <span>【传统预警】{{ data.traditional.alert.msg }}</span>
  <span class="tag-r">上证指数 {{ '%.2f' % data.traditional.last_close }}</span>
</div>

<div class="grid">
  <div class="card full"><h3>上证指数 K 线 + MA5/10/20/60 + BOLL 阈值带（红色虚线 = 上轨压力阈值 / 橙色虚线 = 下轨支撑阈值）</h3>
    <div id="chart_kline" class="chart tall"></div></div>

  <div class="card"><h3>MACD (12,26,9)</h3><div id="chart_macd" class="chart small"></div></div>
  <div class="card"><h3>RSI(14) + BOLL %B</h3><div id="chart_rsi" class="chart small"></div></div>

  <div class="card"><h3>传统指标明细信号</h3>
    <ul class="signals">
      {% for s in data.traditional.alert.signals %}
      <li>{{ s }}</li>
      {% else %}
      <li>无显著信号</li>
      {% endfor %}
    </ul>
  </div>
  <div class="card"><h3>传统预警 · 操作建议</h3>
    <div class="action-banner" style="background:{{ data.traditional.alert.color == 'red' and '#e74c3c' or (data.traditional.alert.color == 'orange' and '#e67e22' or (data.traditional.alert.color == 'gold' and '#f1c40f' or (data.traditional.alert.color == 'gray' and '#95a5a6' or '#27ae60'))) }};color:#fff;padding:10px 14px;border-radius:8px;font-size:15px;font-weight:bold;">
      ▶ {{ data.traditional.alert.action }} <span style="font-weight:normal;font-size:12px;opacity:.9">（建议仓位: {{ data.traditional.alert.pos }}）</span>
    </div>
    <div class="suggestion">{{ data.traditional.alert.suggestion }}</div>
    {% if data.traditional.alert.rationale %}
    <div style="margin-top:10px"><b>分析依据</b>
      <ul class="signals">
        {% for r in data.traditional.alert.rationale %}
        <li>{{ r }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}
    <div style="margin-top:12px">
      <b>当前指标值</b><br>
      <span class="tag">收盘 {{ '%.2f' % data.traditional.last_close }}</span>
      <span class="tag">MA60 {{ '%.2f' % data.traditional.last_ma60 if data.traditional.last_ma60 else '—' }}</span>
      <span class="tag">RSI {{ '%.1f' % data.traditional.last_rsi }}</span>
      <span class="tag">%B {{ '%.2f' % data.traditional.last_pctb if data.traditional.last_pctb else '—' }}</span>
      <span class="tag">KDJ J {{ '%.1f' % data.traditional.last_j }}</span>
    </div>
  </div>
</div>
{% else %}
<div class="card full" style="text-align:center;color:#95a5a6;padding:40px;">{{ data.traditional.alert.msg }}</div>
{% endif %}

<div class="foot">分形数学预判大盘 vs 传统技术指标 · 仅供研究参考，不构成投资建议 · 投资有风险，决策需谨慎</div>

<script>
const DATA = {{ data_json | safe }};

function makeChart(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  const chart = echarts.init(el, null, {renderer:'canvas'});
  return chart;
}

function renderAll() {
  const tl = DATA.timeline;
  const n = tl.window_end.length;
  const xs = Array.from({length:n}, (_,i) => i+1);

  // 1. 簇跳率图 (修复: 显式宽度 + 出框防护)
  const c1 = makeChart('chart_cjr');
  if (c1) {
    try {
    c1.setOption({
      tooltip:{trigger:'axis'},
      legend:{data:['coarse(k=3)','mid(k=5)','fine(k=8)'], top:0},
      grid:{left:55,right:30,top:36,bottom:30,containLabel:false},
      xAxis:{type:'category',data:xs,name:'窗口(每20日)'},
      yAxis:{type:'value',max:100,axisLabel:{formatter:v=>v+'%'}},
      series:[
        {name:'coarse(k=3)',type:'line',data:tl.cjr['3'].map(v=>+(v*100).toFixed(1)),smooth:true,lineWidth:1.5,itemStyle:{color:'#95a5a6'}},
        {name:'mid(k=5)',type:'line',data:tl.cjr['5'].map(v=>+(v*100).toFixed(1)),smooth:true,lineWidth:2.5,itemStyle:{color:'#e67e22'}},
        {name:'fine(k=8)',type:'line',data:tl.cjr['8'].map(v=>+(v*100).toFixed(1)),smooth:true,lineWidth:2.5,itemStyle:{color:'#e74c3c'}},
        {name:'撤退阈值55%',type:'line',data:Array(n).fill(55),lineStyle:{type:'dashed',color:'#e74c3c'},symbol:'none'},
        {name:'警惕阈值40%',type:'line',data:Array(n).fill(40),lineStyle:{type:'dashed',color:'#f39c12'},symbol:'none'}
      ]
    });
    } catch(e) { console.error('chart_cjr:', e); }
  }

  // 2. Hurst / 谱宽
  const c2 = makeChart('chart_hurst');
  if (c2) { try {
    c2.setOption({
      tooltip:{trigger:'axis'}, grid:{left:55,right:20,top:20,bottom:30},
      xAxis:{type:'category',data:xs}, yAxis:{type:'value'},
      series:[{type:'line',data:tl.avg_hurst.map(v=>+v.toFixed(3)),smooth:true,lineWidth:2,
        itemStyle:{color:'#2980b9'},lineStyle:{color:'#2980b9'}}]
    });
  } catch(e) { console.error('chart_hurst:', e); } }
  const c3 = makeChart('chart_width');
  if (c3) { try {
    c3.setOption({
      tooltip:{trigger:'axis'}, grid:{left:55,right:20,top:20,bottom:30},
      xAxis:{type:'category',data:xs}, yAxis:{type:'value'},
      series:[{type:'line',data:tl.avg_width.map(v=>+v.toFixed(3)),smooth:true,lineWidth:2,
        itemStyle:{color:'#8e44ad'},lineStyle:{color:'#8e44ad'}}]
    });
  } catch(e) { console.error('chart_width:', e); } }

  // 3. 簇构成饼图
  const c4 = makeChart('chart_cluster');
  if (c4) { try {
    const comp = DATA.cluster_composition['5'];
    const rows = Object.entries(comp).map(([cl, codes]) => ({
      name:'簇'+cl+' ('+codes.length+'只)', value:codes.length
    }));
    c4.setOption({
      tooltip:{trigger:'item', formatter:'{b}: {c} 只 ({d}%)'},
      series:[{type:'pie', radius:['35%','68%'], data:rows, label:{fontSize:12}, itemStyle:{borderRadius:4}}]
    });
  } catch(e) { console.error('chart_cluster:', e); } }

  // ===== 传统对照区 =====
  if (DATA.trad_ok) {
    const tr = DATA.traditional;
    const dt = tr.date.slice(-120);
  // 4. K线 + MA + BOLL阈值带 + 事件标记
  const c5 = makeChart('chart_kline');
  if (c5) {
    try {
      const closes = tr.close.slice(-120);
      const opens = tr.open.slice(-120);
      const lows = tr.low.slice(-120);
      const highs = tr.high.slice(-120);
      const kdata = closes.map((c,i)=>({value:[dt[i], opens[i], closes[i], lows[i], highs[i]]}));
      // 事件标记点 (markPoint: 用 category 轴索引定位)
      const bollMarks = [];
      tr.boll_events.forEach(ev => {
        const idx = dt.indexOf(ev.date);
        if (idx < 0) return;
        if (ev.type === 'break_up') {
          bollMarks.push({name:'突破上轨', coord:[ev.date, highs[idx]], value:'突破',
            symbol:'pin', symbolSize:26, symbolOffset:[0,-8],
            itemStyle:{color:'#e74c3c'}, label:{formatter:'突破',fontSize:9,color:'#fff'}});
        } else {
          bollMarks.push({name:'跌破下轨', coord:[ev.date, lows[idx]], value:'跌破',
            symbol:'pin', symbolSize:26, symbolOffset:[0,10],
            itemStyle:{color:'#f39c12'}, label:{formatter:'跌破',fontSize:9,color:'#fff'}});
        }
      });
      const macdMarks = [];
      tr.macd_events.forEach(ev => {
        const idx = dt.indexOf(ev.date);
        if (idx < 0) return;
        if (ev.type === 'golden') {
          macdMarks.push({name:'MACD金叉', coord:[ev.date, lows[idx]], value:'金',
            symbol:'triangle', symbolSize:14, symbolOffset:[0,10],
            itemStyle:{color:'#27ae60'}, label:{fontSize:9,color:'#27ae60',position:'bottom'}});
        } else {
          macdMarks.push({name:'MACD死叉', coord:[ev.date, highs[idx]], value:'死',
            symbol:'triangle', symbolSize:14, symbolRotate:180, symbolOffset:[0,-8],
            itemStyle:{color:'#c0392b'}, label:{fontSize:9,color:'#c0392b',position:'top'}});
        }
      });
      c5.setOption({
        tooltip:{trigger:'axis', axisPointer:{type:'cross'}},
        legend:{data:['K线','MA5','MA10','MA20','MA60','BOLL上轨(压力阈值)','BOLL下轨(支撑阈值)'], top:0},
        grid:{left:60,right:30,top:36,bottom:50},
        xAxis:{type:'category',data:dt,axisLabel:{rotate:45,fontSize:10}},
        yAxis:{type:'value',scale:true},
        dataZoom:[{type:'inside'},{type:'slider',height:16,bottom:2}],
        series:[
          {name:'K线',type:'candlestick',data:kdata,itemStyle:{color:'#e74c3c',color0:'#27ae60',borderColor:'#e74c3c',borderColor0:'#27ae60'},
           markPoint:{data:bollMarks.concat(macdMarks)}},
          {name:'MA5',type:'line',data:tr.ma5.slice(-120),smooth:true,symbol:'none',lineStyle:{width:1,color:'#e67e22'}},
          {name:'MA10',type:'line',data:tr.ma10.slice(-120),smooth:true,symbol:'none',lineStyle:{width:1,color:'#2980b9'}},
          {name:'MA20',type:'line',data:tr.ma20.slice(-120),smooth:true,symbol:'none',lineStyle:{width:1,color:'#8e44ad'}},
          {name:'MA60',type:'line',data:tr.ma60.slice(-120),smooth:true,symbol:'none',lineStyle:{width:1.5,color:'#34495e'}},
          {name:'BOLL上轨(压力阈值)',type:'line',data:tr.boll_up.slice(-120),smooth:true,symbol:'none',lineStyle:{type:'dashed',width:1.5,color:'#e74c3c'}},
          {name:'BOLL下轨(支撑阈值)',type:'line',data:tr.boll_low.slice(-120),smooth:true,symbol:'none',lineStyle:{type:'dashed',width:1.5,color:'#f39c12'}}
        ]
      });
    } catch(e) { console.error('chart_kline:', e); }
  }
  // 5. MACD
  const c6 = makeChart('chart_macd');
  if (c6) {
    try {
      c6.setOption({
        tooltip:{trigger:'axis'}, legend:{data:['DIF','DEA','HIST'],top:0},
        grid:{left:55,right:20,top:30,bottom:30},
        xAxis:{type:'category',data:dt,axisLabel:{fontSize:9}},
        yAxis:{type:'value'},
        series:[
          {name:'DIF',type:'line',data:tr.dif.slice(-120),symbol:'none',lineStyle:{width:1.5,color:'#2980b9'}},
          {name:'DEA',type:'line',data:tr.dea.slice(-120),symbol:'none',lineStyle:{width:1.5,color:'#e67e22'}},
          {name:'HIST',type:'bar',data:tr.hist.slice(-120),itemStyle:{color:'#95a5a6'}}
        ]
      });
    } catch(e) { console.error('chart_macd:', e); }
  }
  // 6. RSI + %B
  const c7 = makeChart('chart_rsi');
  if (c7) {
    try {
      c7.setOption({
        tooltip:{trigger:'axis'}, legend:{data:['RSI14','%B'],top:0},
        grid:{left:55,right:20,top:30,bottom:30},
        xAxis:{type:'category',data:dt,axisLabel:{fontSize:9}},
        yAxis:[{type:'value',min:0,max:100},{type:'value',min:0,max:1.5}],
        series:[
          {name:'RSI14',type:'line',data:tr.rsi14.slice(-120),symbol:'none',lineStyle:{width:1.5,color:'#8e44ad'}},
          {name:'%B',type:'line',yAxisIndex:1,data:tr.pctb.slice(-120),symbol:'none',lineStyle:{width:1,color:'#16a085'}},
          {name:'超买70',type:'line',data:Array(120).fill(70),lineStyle:{type:'dashed',color:'#e74c3c'},symbol:'none'},
          {name:'超卖30',type:'line',data:Array(120).fill(30),lineStyle:{type:'dashed',color:'#27ae60'},symbol:'none'}
        ]
      });
    } catch(e) { console.error('chart_rsi:', e); }
  }
  }

  // 统一 resize
  ['chart_cjr','chart_hurst','chart_width','chart_cluster','chart_kline','chart_macd','chart_rsi'].forEach(id=>{
    const c = echarts.getInstanceByDom(document.getElementById(id));
    if (c) c.resize();
  });
}

// 关键修复: 等 window.onload (CSS/字体就绪) 再初始化, 避免宽度计算错误
window.addEventListener('load', () => { setTimeout(renderAll, 50); });
window.addEventListener('resize', () => {
  ['chart_cjr','chart_hurst','chart_width','chart_cluster','chart_kline','chart_macd','chart_rsi'].forEach(id=>{
    const c = echarts.getInstanceByDom(document.getElementById(id));
    if (c) c.resize();
  });
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    data = get_data()
    data_json = json.dumps(data, ensure_ascii=False,
                           default=lambda o: float(o) if hasattr(o, 'item') else
                           (int(o) if isinstance(o, np.integer) else str(o)))
    return render_template_string(PAGE, data=data, data_json=data_json)


@app.route("/api/data")
def api_data():
    return jsonify(get_data(force=True))


if __name__ == "__main__":
    print("=" * 60)
    print("分形大盘预警系统 v1.1 · http://127.0.0.1:5002")
    print(f"分形模式: {'通达信' if TDX_MODE=='tdx' else '模拟数据'}")
    print("传统对照: 上证指数真实数据 (腾讯行情)")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5002, debug=False)
