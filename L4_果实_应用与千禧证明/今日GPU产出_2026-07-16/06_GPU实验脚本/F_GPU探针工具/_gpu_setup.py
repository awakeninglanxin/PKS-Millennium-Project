# -*- coding: utf-8 -*-
"""SSH 批量执行工具"""
import paramiko, sys, time

HOST = 'connect.nmb1.seetacloud.com'
PORT = 12014
USER = 'root'
PASS = 'Ubso9y4t4Vl1'

def ssh_cmd(cmd, timeout=30):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    client.close()
    return out, err

print("=== CuPy 验证 ===")
o, e = ssh_cmd("python3 -c 'import cupy as cp; print(\"CuPy:\", cp.__version__); a=cp.arange(1000000,dtype=cp.float32); b=cp.sum(a); print(\"GPU sum:\", b); print(\"Device:\", cp.cuda.Device(0).name)'", 30)
print(o)
if e: print("ERR:", e[:200])

print("\n=== 后台安装 PyTorch ===")
o, e = ssh_cmd("nohup pip3 install torch --index-url https://download.pytorch.org/whl/cu124 > /tmp/torch_install.log 2>&1 & echo 'PID='$!", 10)
print(o)

print("\n=== 数据盘 ===")
o, e = ssh_cmd("df -h /root/autodl-tmp/ && echo '---' && ls /root/autodl-tmp/", 10)
print(o)
