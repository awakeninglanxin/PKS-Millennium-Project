import re, subprocess, os
od = r'D:\AAA我的文件\PKS_千禧难题_GitHub版\归档_2026-07-18\逆M详细代码\逆M树状代码\05_帕斯卡与莫比乌斯外部映射\分形图像+共形映射'
script = os.path.join(od, 'run_levy_mobius_hexscale.py')
for hs in [0.003, 0.005, 0.007, 0.01]:
    with open(script, 'r') as f: c = f.read()
    c = re.sub(r'HEX_SCALE=[0-9.]+', 'HEX_SCALE=' + str(hs), c, count=1)
    c = re.sub(r'UF22_levy8_mobius_hs[0-9.]+_D', 'UF22_levy8_mobius_hs' + str(hs) + '_D', c)
    with open(script, 'w') as f: f.write(c)
    r = subprocess.run(['C:/Users/ThinkPad/.workbuddy/binaries/python/versions/3.13.12/python.exe', script],
                       cwd=od, capture_output=True, text=True)
    lines = r.stdout.splitlines()
    fill_line = [l for l in lines if l.startswith('fill=')]
    done = [l for l in lines if l.startswith('Done:')]
    msg = fill_line[0] if fill_line else '?'
    done_msg = done[0][:100] if done else '?'
    print(f'hs={hs}: {msg} | {done_msg}')
    if r.returncode != 0:
        print('ERR', r.stderr[-300:])
