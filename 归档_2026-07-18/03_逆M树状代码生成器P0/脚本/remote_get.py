import paramiko, os

HOST = "connect.nmb1.seetacloud.com"
PORT = 34296
USER = "root"
PASS = "HWLtCw+tpNnw"
REMOTE = "/root/inverse_m_work"
LOCAL = r"D:\AAA我的文件\中健国康 NLS细胞检测\未来技术扩展\逆M详细代码\逆M树状代码\逆M树状代码生成器_P0_2026-07-18"

os.makedirs(LOCAL, exist_ok=True)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
            look_for_keys=False, allow_agent=False)
sftp = ssh.open_sftp()
sftp.chdir(REMOTE)
files = [f for f in sftp.listdir() if f.endswith((".png", ".npz", ".json"))]
print(f"发现 {len(files)} 个结果文件:")
for f in files:
    print("  -", f)
print("开始下载 ...")
for f in files:
    sftp.get(f, os.path.join(LOCAL, f))
    print("  GET", f)
sftp.close()
ssh.close()
print("全部下载完成 ->", LOCAL)
