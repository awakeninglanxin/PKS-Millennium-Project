"""
批量武器图生成 第3批 — 覆盖所有剩余1前缀节点图（103个）
自动为每个代码生成prompt：基于节点类型+代码特征配法器/武器
"""
import requests, os, time, re, urllib.parse

OUT_DIR = "D:/AAA我的文件/慈海九宫格_整合版/generated-images"
DEITIES_JS = "D:/AAA我的文件/慈海九宫格_整合版/deities.js"
os.makedirs(OUT_DIR, exist_ok=True)

# ===== 节点类型→法器映射 =====
WEAPONS = {
    "Sanqing": {"weapon": "divine artifact", "desc": "Sanqing celestial"},
    "Sirius": {"weapon": "Sirius energy beacon staff", "desc": "Sirius star mentor"},
    "Orion": {"weapon": "celestial sword or crossbow", "desc": "Orion warrior"},
    "Yahyel": {"weapon": "divine scroll and staff", "desc": "Yahyel prophet"},
    "Pleiades": {"weapon": "star navigation orb", "desc": "Pleiades commander"},
    "Annunaki": {"weapon": "thunderbolt scepter", "desc": "Annunaki divine king"},
    "Gaia": {"weapon": "world tree branch", "desc": "Gaia Earth steward"},
    "Arcturus": {"weapon": "frequency crystal or tuning fork", "desc": "Arcturus elder"},
    "Essassani": {"weapon": "fusion orb", "desc": "Essassani hybrid"},
    "Grey": {"weapon": "crystal staff", "desc": "Grey federation"},
    "Acquired": {"weapon": "acquired celestial artifact", "desc": "Acquired child"},
    "Four_Pure": {"weapon": "jeweled sword or dharma weapon", "desc": "Four Pure King"},
    "Duodenal": {"weapon": "astrolabe with scroll", "desc": "Duodenal guardian"},
    "Innate_Child": {"weapon": "innate divine gem", "desc": "Innate child"},
    "default": {"weapon": "celestial weapon", "desc": "celestial deity"},
}
NODE_KEYWORDS = ["Grey_","Essassani_","Sirius_","Orion_","Yahyel_","Pleiades_","Annunaki_","Gaia_","Arcturus_","Acquired_","Four_Pure_","Sanqing_","Duodecimal_","Innate_Child_"]

# 已知长代码所属类型（提取已有条目中的映射）
with open(DEITIES_JS, 'r', encoding='utf-8') as f:
    FULL_JS = f.read()

def get_node_type(img_path):
    """从节点图文件名推断类型"""
    for kw in NODE_KEYWORDS:
        if kw in img_path:
            return kw.rstrip('_')
    return "default"

def gen_prompt(code, node_type):
    """根据节点类型生成提示词"""
    w = WEAPONS.get(node_type, WEAPONS["default"])
    prompt = f"Code {code} {w['desc']} holding {w['weapon']}, celestial divine being, traditional Chinese art style, glowing aura, high quality, detailed"
    return prompt

# ===== 找出所有1前缀节点图 =====
entries = re.findall(r'code:\"(\d+)\".*?name:\"([^\"]+)\".*?image:\"([^\"]+)\".*?node:(\d+)', FULL_JS)

remaining = []
for code, name, img, nd in entries:
    if not code.startswith('1'):
        continue
    is_node = any(k in img for k in NODE_KEYWORDS)
    is_weapon = 'code_' in img
    if is_node and not is_weapon:
        node_type = get_node_type(img)
        remaining.append((code, name, nd, node_type))

print(f"待生成节点图: {len(remaining)} 个\n")

def gen_image(code, prompt, max_retries=2):
    encoded = urllib.parse.quote(prompt[:500])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&seed={hash(code)%100000}&model=flux"
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 5000:
                fname = f"code_{code}_{int(time.time())}.jpg"
                fpath = os.path.join(OUT_DIR, fname)
                with open(fpath, 'wb') as f:
                    f.write(r.content)
                print(f"  ✅ {code} → {len(r.content)//1024}KB")
                return fname
            else:
                print(f"  ⚠️ {code} attempt {attempt+1}: {r.status_code}")
        except Exception as e:
            print(f"  ❌ {code}: {e}")
        time.sleep(2)
    return None

def update_deities_js(code, fname):
    if not fname: return False
    try:
        with open(DEITIES_JS, 'r', encoding='utf-8') as f:
            js = f.read()
        lines = js.split('\n')
        for i, line in enumerate(lines):
            if f'code:"{code}"' in line and 'image:' in line:
                img_match = re.search(r'(image:")([^"]+)(")', line)
                if img_match:
                    lines[i] = line[:img_match.start(2)] + f"generated-images/{fname}" + line[img_match.end(2):]
                    break
        with open(DEITIES_JS, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True
    except:
        return False

# ===== 分批执行，每10个一报 =====
results = []
batch_size = 10
total = len(remaining)

for batch_start in range(0, total, batch_size):
    batch = remaining[batch_start:batch_start+batch_size]
    print(f"─── 批次 {batch_start//batch_size+1}/{(total-1)//batch_size+1} ({batch_start+1}-{min(batch_start+batch_size,total)}) ───")
    
    for code, name, nd, ntype in batch:
        prompt = gen_prompt(code, ntype)
        print(f"  {code} ({name[:12]}) N{nd} [{ntype}]...", end=" ")
        fname = gen_image(code, prompt)
        if fname:
            ok = update_deities_js(code, fname)
            results.append((code, "✅" if ok else "⚠️"))
            print(f" {'updated' if ok else '关联失败'}")
        else:
            results.append((code, "❌"))
            print(" 失败")
        time.sleep(5)
    
    print(f"  批次完成，已累计 {len(results)}/{total}\n")

print(f"\n{'='*50}")
print(f"全部完成！生成 {len([r for r in results if r[1]!='❌'])}/{total} 个")
matched_1 = len([c for c,n,_,_ in remaining if c.startswith('1')])
print(f"1前缀节点图覆盖率: {matched_1}")
