#!/usr/bin/env python3
"""Probe new Seetacloud GPU environment on port 49303."""
import paramiko, time

host = "connect.nmb1.seetacloud.com"
port = 49303
user = "root"
pwd = "GhRZqpHCblfQ"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    c.connect(host, port, user, pwd, timeout=15)
    print("=== CONNECTED ===", flush=True)
    
    cmds = [
        "nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader",
        "python3 -c 'import torch; print(\"torch\",torch.__version__); print(\"CUDA\",torch.version.cuda)' 2>/dev/null || echo 'no-torch'",
        "python3 -c 'import cupy; print(\"cupy\",cupy.__version__)' 2>/dev/null || echo 'no-cupy'",
        "python3 -c 'import numpy; print(\"numpy\",numpy.__version__)' 2>/dev/null || echo 'no-numpy'",
        "nproc; free -g | head -2",
        "ps -eo pid,etime,cmd | grep python3 | grep -v grep | head -5",
        "ls /root/ 2>/dev/null | head -10",
    ]
    for cmd in cmds:
        i, o, e = c.exec_command(cmd, timeout=15)
        out = o.read().decode().strip()
        err = e.read().decode().strip()
        if out: print(out, flush=True)
        if err: print("ERR:", err[:120], flush=True)
    
    c.close()
except Exception as e:
    print(f"FAIL: {e}", flush=True)
