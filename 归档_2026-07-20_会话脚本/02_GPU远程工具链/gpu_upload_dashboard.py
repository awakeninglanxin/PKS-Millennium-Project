#!/usr/bin/env python3
"""Upload Super k-Shape scripts to GPU and run full experiment"""
import paramiko, os, time

HOST = "connect.nmb1.seetacloud.com"
PORT = 47079
USER = "root"
PWD = "uDUEAL1lw24R"
REMOTE = "/root/super_kshape_work"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, PORT, USER, PWD, timeout=15)
print("Connected", flush=True)

sftp = ssh.open_sftp()
sftp.mkdir(REMOTE)

files = [
    r"C:\Users\ThinkPad\WorkBuddy\2026-07-01-16-57-11\super_kshape.py",
    r"C:\Users\ThinkPad\WorkBuddy\2026-07-01-16-57-11\gpu_dashboard.py",
]
for f in files:
    name = os.path.basename(f)
    sftp.put(f, f"{REMOTE}/{name}")
    print(f"Uploaded: {name} ({os.path.getsize(f)} bytes)")

sftp.close()

# Run
i, o, e = ssh.exec_command(
    f"cd {REMOTE} && python3 gpu_dashboard.py 2>&1", timeout=600)
out = o.read().decode(errors='replace')
err = e.read().decode(errors='replace')
print(out[-3000:])
if err and 'WARNING' not in err[:200]:
    print("STDERR:", err[-500:])

# List outputs
i, o, e = ssh.exec_command(f"ls -la {REMOTE}/super_kshape_results/", timeout=10)
print("\n=== REMOTE OUTPUT ===")
print(o.read().decode())

ssh.close()
print("\nDONE")
