#!/usr/bin/env python3
"""Upload chip scripts to GPU and run them all"""
import paramiko, os, time, sys

HOST = "connect.nmb1.seetacloud.com"
PORT = 49303
USER = "root"
PWD = "GhRZqpHCblfQ"

LOCAL = r"C:\Users\ThinkPad\WorkBuddy\2026-07-01-16-57-11\chip_gpu_scripts"
REMOTE = "/root/chip_work"

def ssh_run(ssh, cmd, timeout=600):
    print(f"  RUN: {cmd[:80]}...", flush=True)
    i, o, e = ssh.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors='replace')
    err = e.read().decode(errors='replace')
    if out: print(out[-500:], flush=True)
    if err and 'WARNING' not in err: print(f"  ERR: {err[-200:]}", flush=True)
    return out

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, PWD, timeout=15)
    print("=== CONNECTED ===\n", flush=True)
    
    # Create workdir
    ssh.exec_command(f"mkdir -p {REMOTE}", timeout=10)
    
    # Upload all scripts via SFTP
    sftp = ssh.open_sftp()
    scripts = [f for f in os.listdir(LOCAL) if f.endswith('.py')]
    for s in scripts:
        local = os.path.join(LOCAL, s)
        remote = f"{REMOTE}/{s}"
        sftp.put(local, remote)
        print(f"  UPLOADED: {s} ({os.path.getsize(local)} bytes)")
    sftp.close()
    print(f"\n=== {len(scripts)} scripts uploaded ===\n", flush=True)
    
    # Run in sequence
    print("=== RUNNING STANDARD SCRIPTS ===", flush=True)
    
    # Standard scripts (fast, CPU)
    std_scripts = [
        "逆M调度算法全集对比.py",
        "三调度器正式实现_五场景对比.py",
        "灾难恢复_真实故障注入仿真.py",
        "Sharkovsky_Agent调度器原型.py",
    ]
    
    for s in std_scripts:
        print(f"\n--- {s} ---", flush=True)
        ssh_run(ssh, f"cd {REMOTE} && python3 {s} 2>&1", timeout=300)
    
    # Farey layout generator (needs matplotlib)
    print(f"\n--- Farey_版图数据集生成器.py ---", flush=True)
    ssh_run(ssh, f"cd {REMOTE} && python3 Farey_版图数据集生成器.py 2>&1", timeout=120)
    
    # Hybrid scheduler (mock input)
    print(f"\n--- hybrid_scheduler.py ---", flush=True)
    ssh_run(ssh, f"cd {REMOTE} && python3 -c \"import hybrid_scheduler; s=hybrid_scheduler.FareyHybridScheduler(); s.load_timing_report(None); print('hybrid_scheduler imported OK')\" 2>&1", timeout=60)
    
    # GPU enhanced runner
    print("\n=== GPU ENHANCED RUNNER (50K rounds × 1000-node DAG) ===", flush=True)
    gpu_out = ssh_run(ssh, f"cd {REMOTE} && python3 gpu_enhanced_runner.py 2>&1", timeout=600)
    
    # List all outputs
    print("\n=== OUTPUT FILES ===", flush=True)
    ssh_run(ssh, f"ls -la {REMOTE}/", timeout=10)
    ssh_run(ssh, f"du -sh {REMOTE}/", timeout=10)
    
    ssh.close()
    print("\n=== DONE ===", flush=True)
    
except Exception as e:
    print(f"FAIL: {e}", flush=True)
    import traceback; traceback.print_exc()
