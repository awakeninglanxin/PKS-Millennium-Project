import paramiko

HOST = "connect.nmb1.seetacloud.com"
PORT = 34296
USER = "root"
PASS = "HWLtCw+tpNnw"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
            look_for_keys=False, allow_agent=False)

cmds = [
    "echo '=== PID 2168 ==='; ps -o pid,ppid,user,etime,pcpu,pmem,cmd -p 2168 2>/dev/null; echo '--- cmdline ---'; tr '\\0' ' ' < /proc/2168/cmdline 2>/dev/null; echo",
    "echo '=== compute apps ==='; nvidia-smi --query-compute-apps=pid,used_memory,process_name --format=csv 2>/dev/null",
    "echo '=== mkdir workdir ==='; mkdir -p /root/inverse_m_work && echo 'workdir ready: /root/inverse_m_work'; ls -la /root/inverse_m_work",
]
for c in cmds:
    print("$ " + c)
    stdin, stdout, stderr = ssh.exec_command(c, timeout=60)
    print(stdout.read().decode(errors="replace"))
    e = stderr.read().decode(errors="replace")
    if e.strip():
        print("[ERR]", e)
    print("-" * 60)

ssh.close()
print("DONE")
