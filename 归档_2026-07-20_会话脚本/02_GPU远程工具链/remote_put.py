import paramiko, sys

HOST = "connect.nmb1.seetacloud.com"
PORT = 34296
USER = "root"
PASS = "HWLtCw+tpNnw"

# 用法: remote_put.py <local> <remote>
local = sys.argv[1]
remote = sys.argv[2]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
            look_for_keys=False, allow_agent=False)
sftp = ssh.open_sftp()
sftp.put(local, remote)
print(f"PUT {local} -> {remote}")
sftp.close()
ssh.close()
