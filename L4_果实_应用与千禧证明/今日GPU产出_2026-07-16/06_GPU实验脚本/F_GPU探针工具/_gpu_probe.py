# -*- coding: utf-8 -*-
"""连接 GPU 服务器并检测硬件"""
import paramiko
import sys

HOST = 'connect.nmb1.seetacloud.com'
PORT = 12014
USER = 'root'
PASS = 'Ubso9y4t4Vl1'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"连接 {HOST}:{PORT} ...")
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    print("✅ 连接成功\n")

    cmds = [
        "nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null",
        "nproc",
        "free -h | head -2",
        "python3 -c 'import torch; print(\"PyTorch:\", torch.__version__, \"CUDA:\", torch.cuda.is_available())' 2>/dev/null || echo 'PyTorch 未安装'",
        "ls /root/autodl-tmp/ 2>/dev/null | head -5",
        "df -h /root/autodl-tmp/ 2>/dev/null | tail -1",
        "pip3 list 2>/dev/null | grep -iE 'torch|cuda|numpy|scipy|mpmath' | head -10",
    ]
    for cmd in cmds:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(out)
        if err:
            print(f"  (stderr: {err[:100]})")
        print()

    client.close()
except Exception as e:
    print(f"❌ 失败: {e}")
    sys.exit(1)
