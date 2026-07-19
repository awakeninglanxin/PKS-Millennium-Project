# -*- coding: utf-8 -*-
"""抓取真实 GRCh38 参考基因组序列(健康野生型) → JSON, 供健康密码音乐网页嵌入"""
import urllib.request, json, time, sys

def get(url, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Accept':'text/plain,application/json'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'ignore')
        except Exception as e:
            print(f'  重试{k+1}: {e.__class__.__name__}', file=sys.stderr); time.sleep(1.5)
    return None

EN = 'https://rest.ensembl.org'
out = {'mt': None, 'genes': []}

# 1) 线粒体完整基因组 (rCRS, chr MT, 16569bp) —— 完整健康参考基因组
print('抓取线粒体完整基因组 MT:1..16569 ...')
mt = get(EN + '/sequence/region/human/MT:1..16569?content-type=text/plain')
if mt:
    mt = ''.join(c for c in mt.upper() if c in 'ACGTN')
    out['mt'] = mt
    print(f'  线粒体: {len(mt)} bp')

# 2) 各染色体地标基因 CDS (真实野生型编码序列)
GENES = [
 ('1','MTHFR'),('2','ALMS1'),('3','VHL'),('4','HTT'),('5','APC'),
 ('6','HLA-A'),('7','CFTR'),('8','MYC'),('9','ABO'),('10','PTEN'),
 ('11','HBB'),('12','KRAS'),('13','BRCA2'),('14','AKT1'),('15','OCA2'),
 ('16','HBA1'),('17','TP53'),('18','SMAD4'),('19','APOE'),('20','ADA'),
 ('21','APP'),('22','NF2'),('X','DMD'),('Y','SRY'),
]
CAP = 900  # 每基因截取前900nt=300密码子(可听长度)
for chrom, sym in GENES:
    print(f'抓取 chr{chrom} {sym} ...')
    lk = get(EN + f'/lookup/symbol/homo_sapiens/{sym}?expand=1;content-type=application/json')
    if not lk:
        print(f'  ✗ lookup失败'); continue
    try:
        info = json.loads(lk)
    except Exception:
        print(f'  ✗ JSON解析失败'); continue
    tid = info.get('canonical_transcript')
    if not tid and info.get('Transcript'):
        tid = info['Transcript'][0]['id']
    if not tid:
        print(f'  ✗ 无转录本'); continue
    tid = tid.split('.')[0]
    cds = get(EN + f'/sequence/id/{tid}?type=cds;content-type=text/plain')
    if not cds:
        print(f'  ✗ CDS失败'); continue
    cds = ''.join(c for c in cds.upper() if c in 'ACGTN')
    full_len = len(cds)
    cds = cds[:CAP]
    out['genes'].append({
        'chr': chrom, 'sym': sym, 'tid': tid,
        'seq': cds, 'full_len': full_len
    })
    print(f'  ✓ {sym}: 全长{full_len}nt, 截取{len(cds)}nt')
    time.sleep(0.25)

json.dump(out, open('/tmp/health_dna.json','w',encoding='utf-8'), ensure_ascii=False)
print(f"\n完成: 线粒体{'✓' if out['mt'] else '✗'}, 基因{len(out['genes'])}/24")
