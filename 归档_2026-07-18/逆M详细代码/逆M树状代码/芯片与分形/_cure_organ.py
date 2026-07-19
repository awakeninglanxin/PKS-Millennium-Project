import struct, os
from collections import Counter

def parse(path):
    with open(path, 'rb') as f: data = f.read()
    pos = 24; out = []
    while pos + 16 <= len(data):
        ts_sec, ts_usec = struct.unpack('<II', data[pos:pos+8])
        cap_len, orig_len = struct.unpack('<II', data[pos+8:pos+16])
        pos += 16
        if cap_len == 0 or cap_len > 50000: break
        hlen = data[pos]
        if hlen not in (27,28): pos+=cap_len; continue
        dl = cap_len - hlen
        if dl == 128:
            cmd = data[pos+hlen:pos+hlen+128]
            b9,b11,b13,b15 = cmd[9],cmd[11],cmd[13],cmd[15]
            if 1<=b9<=35:
                out.append({'b9':b9,'b11':b11,'b13':b13,'b15':b15,'ts':ts_sec+ts_usec/1e6})
        pos += cap_len
    return out

B9_MAP = {1:('极低频/基础','水'),2:('极低频/共振','水'),3:('极低频/调和','水'),
    4:('超低频/A','水'),5:('超低频/B','水'),6:('低频/A','土'),7:('低频/B','土'),
    8:('中低频/A','土'),9:('中低频/B','土'),10:('中频/A','土'),11:('中频/B','土'),
    12:('中高频/A','金'),13:('中高频/B','金'),14:('高频/A','金'),15:('高频/B','金'),
    16:('超高频/A','金'),17:('淋巴/免疫','火'),18:('肌肉/结缔','火'),
    19:('脑/中枢','火'),20:('皮肤/皮毛','火'),21:('心血管','火'),
    22:('消化/胃部','木'),23:('消化/肠道','木'),24:('消化/肝脏','木'),
    25:('消化/胰腺','木'),26:('甲状腺','木'),27:('呼吸/肺','木'),
    28:('泌尿/肾','木'),29:('极高频/调和','木'),30:('低频/C','木'),
    31:('中低频/C','木'),32:('中高频/C','木'),33:('中频/C','木'),
    34:('高频/C','木'),35:('超高频/C','木')}

cmds = parse(r'D:\AAA我的文件\中健国康 NLS细胞检测\我的pdf\明锜\nls_cmq2cure')

groups = []; g = [cmds[0]]
for i in range(1,len(cmds)):
    if cmds[i]['ts'] - cmds[i-1]['ts'] > 0.5:
        groups.append(g); g = [cmds[i]]
    else: g.append(cmds[i])
groups.append(g)

print(f'Total groups: {len(groups)}')
print()

treat_groups = []
for i, g in enumerate(groups):
    b9s = sorted(set(c['b9'] for c in g))
    same = sum(1 for c in g if c['b9']==c['b13'])
    b11s = [c['b11'] for c in g]
    b15s = [c['b15'] for c in g]
    is_treat = any(abs(c['b11']-15)>5 or abs(c['b15']-15)>5 for c in g)
    
    if is_treat:
        top_b9 = Counter(c['b9'] for c in g).most_common(1)[0][0]
        organ = B9_MAP.get(top_b9, ('?','?'))[0]
        treat_groups.append({
            'idx': i, 'b9s': b9s, 'organ': organ,
            'same': same, 'total': len(g),
            'amps': (min(b11s), max(b11s), min(b15s), max(b15s))
        })
        print(f'组{i:3d} [疗愈] b9={b9s[:5]} 同频{same}/{len(g)} {organ} b11={min(b11s)}-{max(b11s)} b15={min(b15s)}-{max(b15s)}')

print(f'\n疗愈组总数: {len(treat_groups)}')
# Organ frequency
org_b9 = Counter(g['organ'] for g in treat_groups)
print('\n被治疗器官统计:')
for org, cnt in org_b9.most_common(20):
    print(f'  {org}: {cnt}次')
