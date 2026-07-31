# -*- coding: utf-8 -*-
"""gpu2_helper.py — Seetacloud GPU (port 20220) 远程执行助手
用法:
  python gpu2_helper.py probe                  # 探测环境
  python gpu2_helper.py run "<cmd>" [timeout]  # 远程执行
  python gpu2_helper.py put <local> <remote>   # SFTP 上传
  python gpu2_helper.py get <remote> <local>   # SFTP 下载 (独立连接, 铁律76)
"""
import sys
import paramiko

HOST = "connect.nmb1.seetacloud.com"
PORT = 20220
USER = "root"
PWD = "fRvc+sJM7AEd"


def connect():
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username=USER, password=PWD,
                timeout=30, banner_timeout=30, auth_timeout=30,
                look_for_keys=False, allow_agent=False)
    return cli


def run(cmd, timeout=120):
    cli = connect()
    try:
        _, out, err = cli.exec_command(cmd, timeout=timeout)
        o = out.read().decode("utf-8", "replace")
        e = err.read().decode("utf-8", "replace")
        rc = out.channel.recv_exit_status()
        print(o)
        if e.strip():
            print("--- STDERR ---")
            print(e)
        print(f"--- exit {rc} ---")
    finally:
        cli.close()


def put(local, remote):
    cli = connect()
    try:
        sftp = cli.open_sftp()
        sftp.put(local, remote)
        st = sftp.stat(remote)
        print(f"uploaded {local} -> {remote} ({st.st_size} bytes)")
        sftp.close()
    finally:
        cli.close()


def get(remote, local):
    cli = connect()
    try:
        sftp = cli.open_sftp()
        sftp.get(remote, local)
        print(f"downloaded {remote} -> {local}")
        sftp.close()
    finally:
        cli.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if mode == "probe":
        run("hostname; echo ---; nvidia-smi; echo ---; "
            "nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv; "
            "echo ---; python3 -V; python3 -c \"import numpy,sys;print('numpy',numpy.__version__)\" 2>&1; "
            "python3 -c \"import cupy;print('cupy',cupy.__version__)\" 2>&1 | head -2; "
            "python3 -c \"import torch;print('torch',torch.__version__, torch.cuda.is_available())\" 2>&1 | head -2; "
            "echo ---; free -g | head -2; nproc; df -h /root | tail -1")
    elif mode == "run":
        run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120)
    elif mode == "put":
        put(sys.argv[2], sys.argv[3])
    elif mode == "get":
        get(sys.argv[2], sys.argv[3])
