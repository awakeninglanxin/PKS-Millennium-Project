import paramiko, sys

HOST = "connect.nmb1.seetacloud.com"
PORT = 34296
USER = "root"
PASS = "HWLtCw+tpNnw"

cmds = [
    "echo '=== hostname / uname ==='; hostname; uname -a",
    "echo '=== nvidia-smi ==='; nvidia-smi 2>/dev/null | head -n 25 || echo 'NO nvidia-smi'",
    "echo '=== nvcc ==='; nvcc --version 2>/dev/null | tail -n 3 || echo 'NO nvcc'",
    "echo '=== python ==='; python3 --version; which python3",
    "echo '=== pip pkgs ==='; python3 -c \"import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.version.cuda if torch.cuda.is_available() else 'n/a')\" 2>/dev/null || echo 'no torch'",
    "python3 -c \"import cupy; print('cupy', cupy.__version__)\" 2>/dev/null || echo 'no cupy'",
    "python3 -c \"import numpy; print('numpy', numpy.__version__)\" 2>/dev/null || echo 'no numpy'",
    "python3 -c \"import matplotlib; print('matplotlib', matplotlib.__version__)\" 2>/dev/null || echo 'no matplotlib'",
    "echo '=== disk / cwd ==='; pwd; df -h / 2>/dev/null | tail -n 2; nproc; free -h 2>/dev/null | head -n 2",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30, look_for_keys=False, allow_agent=False)
print("CONNECTED OK\n")

for c in cmds:
    print(f"$ {c}")
    stdin, stdout, stderr = ssh.exec_command(c, timeout=60)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    print(out)
    if err.strip():
        print("[err]", err)
    print("-" * 60)

ssh.close()
print("DONE")
