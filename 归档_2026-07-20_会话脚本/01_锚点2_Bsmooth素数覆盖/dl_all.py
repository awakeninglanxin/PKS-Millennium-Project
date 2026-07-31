import paramiko, os
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect("connect.nmb1.seetacloud.com", port=20220, username="root", password="fRvc+sJM7AEd",
            timeout=30, look_for_keys=False, allow_agent=False)
sftp = cli.open_sftp()
DIST = r"D:\AAA我的文件\PKS_千禧难题_GitHub版\锚点2_GPU验证结果_2026-07-18"
sftp.chdir("/root/smooth_work")
for f in sorted(sftp.listdir()):
    if f.startswith("miss_") or f.endswith(".jsonl") or f == "ladder.log":
        remote = f"/root/smooth_work/{f}"
        local = os.path.join(DIST, f)
        print(f"  {f} -> {local}")
        sftp.get(remote, local)
sftp.close(); cli.close()
print("DONE")
