"""
B.T.S.E. v2 — 真数据版 最终版
==============================
沪深300抽样32只 → 真实日K → LiquidODE+MF-DFA → 多尺度切树 → 行业/HMM评估
"""
import json, subprocess, time, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0,"/data/workspace")
from btse_v2_pipeline import (
    LiquidODEEncoder, extract_signatures, rolling_windows,
    global_normalize, signature_distance, agglomerative_cluster
)

# ---- 样本 ----
SAMPLE = [
    ("sh601318","中国平安","金融"),("sh601988","中国银行","金融"),
    ("sh601166","兴业银行","金融"),("sh600030","中信证券","金融"),
    ("sh600036","招商银行","金融"),
    ("sh600519","贵州茅台","食品饮料"),("sz000858","五粮液","食品饮料"),
    ("sz000568","泸州老窖","食品饮料"),("sh600887","伊利股份","食品饮料"),
    ("sh600276","恒瑞医药","医药生物"),("sh601607","上海医药","医药生物"),
    ("sz300760","迈瑞医疗","医药生物"),
    ("sh601012","隆基绿能","电力设备"),("sz300274","阳光电源","电力设备"),
    ("sh600406","国电南瑞","电力设备"),
    ("sz002594","比亚迪","汽车"),("sh601633","长城汽车","汽车"),
    ("sz000625","长安汽车","汽车"),("sh600104","上汽集团","汽车"),
    ("sh600741","华域汽车","汽车"),
    ("sh601899","紫金矿业","有色金属"),("sh600362","江西铜业","有色金属"),
    ("sh603993","洛阳钼业","有色金属"),
    ("sh600028","中国石化","石油石化"),("sh601857","中国石油","石油石化"),
    ("sh600900","长江电力","公用事业"),
    ("sh601728","中国电信","通信"),
    ("sz002230","科大讯飞","计算机"),
    ("sh688012","中微公司","电子"),("sz002475","立讯精密","电子"),
    ("sh688041","海光信息","电子"),
    ("sz300059","东方财富","非银金融"),
]

def fetch_kline(code, start="2023-01-01", end="2026-07-21"):
    cmd = ["node","/data/skills/westock-data/scripts/index.js",
           "kline",code,"--period","day","--limit","1500","--raw"]
    last_err=""
    for _ in range(3):
        try:
            out=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
        except Exception as e:
            last_err=str(e); time.sleep(2); continue
        if out.returncode!=0: last_err=out.stderr[:120]; time.sleep(2); continue
        txt=out.stdout.strip()
        if not txt: last_err="empty"; time.sleep(2); continue
        try: data=json.loads(txt)
        except Exception as e: last_err=f"json:{e}"; time.sleep(2); continue
        if isinstance(data,dict):
            for v in data.values():
                if isinstance(v,list) and len(v)>0: data=v; break
        if not isinstance(data,list): last_err=f"not list"; time.sleep(2); continue
        rows=[]
        for r in data:
            d=r.get("date") or r.get("day") or r.get("日期")
            if not d: continue
            if start<=str(d)<=end:
                try:
                    c=float(r.get("last") or r.get("close") or 0)
                    v=float(r.get("volume") or 0)
                    if c>0: rows.append({"date":str(d),"close":c,"volume":v})
                except: pass
        if rows: return rows
        last_err=f"0 rows (raw n={len(data)})"; time.sleep(1)
    return []

def main():
    t0=time.time()
    outdir="/data/workspace/btse_v2_output"
    os.makedirs(outdir,exist_ok=True)
    print("="*60)
    print("B.T.S.E. v2 — 真数据版 (沪深300抽样32只)")
    print("="*60)

    panel={}
    print("\n[1/5] 拉取K线 2023-01-01~2026-07-21 ...")
    for code,name,ind in SAMPLE:
        rows=fetch_kline(code)
        if len(rows)<250:
            print(f"  ✗ {code} {name} {len(rows)}条"); continue
        c=np.array([r["close"] for r in rows],float)
        v=np.array([r["volume"] for r in rows],float)
        ret=np.diff(np.log(c)); v=v[1:]
        if len(ret)<200: continue
        panel[code]={"name":name,"industry":ind,"return":ret,"volume":v}
        print(f"  ✓ {code} {name:6s} {ind:6s} T={len(ret)}")

    print(f"\n成功 {len(panel)} 只")
    ind_cnt=defaultdict(int)
    for d in panel.values(): ind_cnt[d["industry"]]+=1
    print("行业:",dict(ind_cnt))

    print("\n[2/5] LiquidODE+MF-DFA 签名...")
    enc=LiquidODEEncoder(8,6,4)
    WIN,STEP=120,20
    records=[]
    for code,d in panel.items():
        for rs,vs,s in rolling_windows(d["return"],d["volume"],WIN,STEP):
            sig=extract_signatures(rs,vs,enc)
            records.append({"code":code,"name":d["name"],
                           "industry":d["industry"],"start_idx":s,"sig":sig})
    sigs=global_normalize([r["sig"] for r in records])
    N=len(records)
    print(f"样本数 N={N}")

    print("[3/5] 距离矩阵...")
    D=np.zeros((N,N))
    for i in range(N):
        for j in range(i+1,N):
            v=signature_distance(sigs[i],sigs[j]); D[i,j]=D[j,i]=v

    print("[4/5] Ward 三档切树...")
    cuts={"coarse":3,"mid":5,"fine":8}
    labels={k:agglomerative_cluster(D,v) for k,v in cuts.items()}
    for i,r in enumerate(records):
        r["labels"]={k:int(labels[k][i]) for k in cuts}
        r["mid"]=r["labels"]["mid"]

    # code→众数簇（labels["mid"] 是标量）
    c2s=defaultdict(list)
    for r in records: c2s[r["code"]].append(r)
    c2c={}
    for c,ss in c2s.items():
        c2c[c]=Counter(int(r["labels"]["mid"]) for r in ss).most_common(1)[0][0]

    # HMM GT
    sv=np.array([np.std(r["sig"]["ode_joint"]) for r in records])
    q33,q66=np.percentile(sv,[33,66])
    hmm=np.zeros(N,int)
    hmm[sv>q66]=2; hmm[(sv>q33)&(sv<=q66)]=1
    ind_vec=np.array([hash(r["industry"])%1000 for r in records])

    print("\n[5/5] 评估")
    metrics={}
    for name in ["coarse","mid","fine"]:
        lb=labels[name]
        ari=adjusted_rand_score(hmm,lb)
        nmi=normalized_mutual_info_score(hmm,lb)
        K=max(lb)+1
        best=sum(cnts.max() for k in range(K)
                if (m:=lb==k).sum()>0
                for _,cnts in [np.unique(ind_vec[m],return_counts=True)])
        pur=best/N
        metrics[name]={"ARI(HMM)":ari,"NMI(HMM)":nmi,"Purity(ind)":pur,"k":K}
        print(f"  [{name:6s}] k={K}  ARI(HMM)={ari:.3f}  NMI(HMM)={nmi:.3f}  Purity(ind)={pur:.3f}")

    # 簇×行业
    ind_names=sorted(set(r["industry"] for r in records))
    K=max(labels["mid"])+1
    mat=np.zeros((K,len(ind_names)))
    for r in records:
        mat[r["labels"]["mid"],ind_names.index(r["industry"])]+=1

    # within/between 相关
    codes=sorted(c for c in panel if c in c2c)
    L=min(len(panel[c]["return"]) for c in codes)
    Rmat=np.array([panel[c]["return"][:L] for c in codes])
    C=np.corrcoef(Rmat)
    w,b=[],[]
    for i in range(len(codes)):
        for j in range(i+1,len(codes)):
            if c2c[codes[i]]==c2c[codes[j]]: w.append(C[i,j])
            else: b.append(C[i,j])
    mw=float(np.mean(w)) if w else 0.0
    mb=None
    if b:
        try: mb=float(np.mean(b))
        except: mb=None
    print(f"\n  簇内相关 均值={mw:.3f} (n={len(w)})")
    print(f"  簇间相关 均值={mb:.3f} (n={len(b)})")

    # ===== 可视化 =====
    # 距离矩阵
    fig,ax=plt.subplots(figsize=(10,9))
    order=np.argsort(labels["mid"])
    Ds=D[np.ix_(order,order)]
    im=ax.imshow(Ds,cmap="viridis",aspect="equal")
    lb=labels["mid"][order]
    bd=[0]+[i for i in range(1,len(lb)) if lb[i]!=lb[i-1]]+[len(lb)]
    for x in bd: ax.axhline(x,c="white",lw=0.5,alpha=0.6); ax.axvline(x,c="white",lw=0.5,alpha=0.6)
    plt.colorbar(im,ax=ax,label="签名距离")
    ax.set_title("真数据 — 距离矩阵 (mid 排序)",fontsize=13)
    fig.tight_layout(); fig.savefig(f"{outdir}/real_distance.png",dpi=130)

    # 簇×行业
    fig,ax=plt.subplots(figsize=(12,5.5))
    im=ax.imshow(mat,cmap="YlOrRd",aspect="auto")
    ax.set_xticks(range(len(ind_names)))
    ax.set_xticklabels(ind_names,rotation=35,ha="right")
    ax.set_yticks(range(K))
    ax.set_yticklabels([f"C{k}" for k in range(K)])
    plt.colorbar(im,ax=ax,label="样本数")
    ax.set_title("真数据 — 簇(mid) × 行业 交叉热力图",fontsize=13)
    fig.tight_layout(); fig.savefig(f"{outdir}/real_cluster_industry.png",dpi=130)

    # PCA
    feats=np.array([np.concatenate([sigs[i]["hq"],sigs[i]["ode_joint"]]) for i in range(N)])
    proj=PCA(2).fit_transform(feats)
    fig,axes=plt.subplots(1,3,figsize=(15,4.5),sharey=True)
    for ax,name in zip(axes,["coarse","mid","fine"]):
        lb=labels[name]
        for k in sorted(set(lb)):
            m=lb==k
            ax.scatter(proj[m,0],proj[m,1],s=12,label=f"{name}-C{k}",alpha=0.8)
        ax.set_title(f"{name} (k={max(lb)+1})"); ax.set_xlabel("PC1")
    axes[0].set_ylabel("PC2")
    fig.suptitle("真数据 — 签名空间 PCA × 多尺度切树",fontsize=13,y=1.01)
    fig.tight_layout(); fig.savefig(f"{outdir}/real_pca_cuts.png",dpi=130)

    # 价格路径着色
    fig,ax=plt.subplots(figsize=(13,7))
    cmap=plt.cm.tab10
    for code in sorted(panel):
        if code not in c2c: continue
        d=panel[code]
        ax.plot(np.cumsum(d["return"]),alpha=0.7,lw=1.0,
                label=f"{d['name']}(C{c2c[code]})",color=cmap(c2c[code]%10))
    ax.set_xlabel("交易日(2023-01起)"); ax.set_ylabel("累计对数收益")
    ax.set_title("真数据 — 各票对数价格路径（颜色=mid簇）",fontsize=13)
    # 图例只列簇
    h,l=ax.get_legend_handles_labels()
    by_k={}
    for hi,li in zip(h,l):
        try:
            k=li.split("(C")[-1].rstrip(")")
            by_k.setdefault(k,hi)
        except: pass
    ax.legend([by_k[k] for k in sorted(by_k)],
              [f"簇{k}" for k in sorted(by_k)],loc="upper left",fontsize=10)
    fig.tight_layout(); fig.savefig(f"{outdir}/real_price_paths.png",dpi=130)

    # within vs between 直方图
    fig,ax=plt.subplots(figsize=(8,5))
    if b: ax.hist(b,bins=20,alpha=0.6,label=f"簇间(n={len(b)})",color="#1f77b4")
    if w: ax.hist(w,bins=20,alpha=0.6,label=f"簇内(n={len(w)})",color="#d62728")
    ax.set_xlabel("return 序列 Pearson 相关")
    ax.set_ylabel("对数价格路径数")
    ax.set_title("真数据 — 簇内 vs 簇间 相关性分布",fontsize=13)
    ax.legend()
    fig.tight_layout(); fig.savefig(f"{outdir}/real_within_between.png",dpi=130)

    # 报告
    elapsed=round(time.time()-t0,2)
    report={
        "config":{"source":"westock-data 腾讯自选股",
                  "universe":"沪深300抽样32只",
                  "n_stocks":len(panel),
                  "industries":dict(ind_cnt),
                  "date_range":"2023-01-01~2026-07-21",
                  "WIN":WIN,"STEP":STEP,"n_samples":N},
        "encoder":"LiquidODE (8f/6m/4s)",
        "signatures":["ode_fast/mid/slow/joint","hq(11)","width","hurst","tail_alpha"],
        "clustering":"Ward + 3 cuts (3/5/8)",
        "ground_truth":"HMM vol-regime + 行业",
        "metrics":metrics,
        "within_cluster_corr_mean":float(mw),
        "between_cluster_corr_mean":float(mb) if b else None,
        "n_within":len(w),"n_between":len(b),
        "elapsed_sec":elapsed,
    }
    with open(f"{outdir}/real_report.json","w") as f:
        json.dump(report,f,indent=2,default=str)
    print(f"\n[done] 耗时 {elapsed}s  产物 → {outdir}/")
    print(json.dumps(report,indent=2,default=str)[:1500])

if __name__=="__main__":
    main()
