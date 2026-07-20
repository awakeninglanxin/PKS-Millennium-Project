# -*- coding: utf-8 -*-
import paramiko, json, time

HOST, PORT, USER, PASS = 'connect.nmb1.seetacloud.com', 27341, 'root', 'XbnjTp5HSnvS'

def ssh(cmd, timeout=60):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    c.close()
    return o, e

print("=== GPU 硬件 ===")
o, e = ssh("nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null && echo '---' && nproc && free -h | head -2 && echo '---' && df -h /root/autodl-tmp/ | tail -1")
print(o)

print("\n=== Python 环境 ===")
o, e = ssh("python3 -c 'import cupy as cp; print(\"CuPy:\", cp.__version__); print(\"Device:\", cp.cuda.Device(0).compute_capability)' 2>/dev/null; python3 -c 'import torch; print(\"PyTorch:\", torch.__version__, \"CUDA:\", torch.cuda.is_available())' 2>/dev/null || echo 'PyTorch未装'")
print(o)
