import paramiko, sys

HOST = "connect.nmb1.seetacloud.com"
PORT = 34296
USER = "root"
PASS = "HWLtCw+tpNnw"

def run(cmd, timeout=120):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
                look_for_keys=False, allow_agent=False)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    ssh.close()
    return out, err

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "echo hi"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    out, err = run(cmd, timeout)
    sys.stdout.write(out)
    if err.strip():
        sys.stderr.write("[ERR]\n" + err)
