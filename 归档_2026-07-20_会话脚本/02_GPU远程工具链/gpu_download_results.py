#!/usr/bin/env python3
"""Download Super k-Shape results and science dashboard figures from GPU"""
import paramiko, os, glob

LOCAL = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\02_应用科技\30_芯片架构与调度算法\Super_kShape_GPU实验_2026-07-20"
os.makedirs(LOCAL, exist_ok=True)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("connect.nmb1.seetacloud.com", 47079, "root", "uDUEAL1lw24R", timeout=15)
print("Connected", flush=True)

sftp = ssh.open_sftp()
REMOTE = "/root/super_kshape_work/super_kshape_results"

# List remote files
i, o, e = ssh.exec_command(f"ls {REMOTE}/", timeout=10)
remote_files = o.read().decode().strip().split('\n')
print(f"Remote files: {len(remote_files)}")

for fname in remote_files:
    fname = fname.strip()
    if not fname: continue
    remote_path = f"{REMOTE}/{fname}"
    local_path = os.path.join(LOCAL, fname)
    try:
        sftp.get(remote_path, local_path)
        size = os.path.getsize(local_path) / 1024
        print(f"  ↓ {fname} ({size:.0f} KB)")
    except Exception as e:
        print(f"  ✗ {fname}: {e}")

sftp.close()

# Also download source scripts
sftp2 = ssh.open_sftp()
for script in ["super_kshape.py", "gpu_dashboard.py"]:
    try:
        sftp2.get(f"/root/super_kshape_work/{script}", os.path.join(LOCAL, script))
        print(f"  ↓ {script}")
    except: pass
sftp2.close()

ssh.close()

# Summary
all_local = glob.glob(f"{LOCAL}/*")
print(f"\n=== Downloaded: {len(all_local)} files to {LOCAL} ===")
for f in sorted(all_local):
    print(f"  {os.path.basename(f)}")
