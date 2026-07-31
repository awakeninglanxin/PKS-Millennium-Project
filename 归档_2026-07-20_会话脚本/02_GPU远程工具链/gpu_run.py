import paramiko, sys, time

HOST = "connect.nmb1.seetacloud.com"
PORT = 34296
USER = "root"
PASS = "HWLtCw+tpNnw"

# 从第二个参数取命令, 否则用默认(小规模验证)
if len(sys.argv) > 1:
    cmd = sys.argv[1]
else:
    cmd = ('cd /root/inverse_m_work && python3 inverse_m_tree.py '
           '--c=-0.74543+0.11301j --depth 4 --gpu --npoints 200000 --nsteps 25')

print("REMOTE CMD:", cmd)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
            look_for_keys=False, allow_agent=False)
t0 = time.time()
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=600)
# 流式读出
import select
while True:
    r, _, _ = select.select([stdout.channel], [], [], 1.0)
    if r:
        line = stdout.channel.recv(4096).decode(errors="replace")
        if not line:
            break
        sys.stdout.write(line)
        sys.stdout.flush()
    if stdout.channel.exit_status_ready() and not stdout.channel.recv_ready():
        break
err = stderr.read().decode(errors="replace")
if err.strip():
    print("[ERR]\n" + err)
print(f"\n[done in {time.time()-t0:.1f}s]")
ssh.close()
