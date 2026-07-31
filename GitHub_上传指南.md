# PKS 千禧项目 — GitHub 上传完整指南

## 当前状态

✅ Git 仓库已初始化  
✅ `.gitignore` 已配置（排除 PDF/DOCX/PPTX/MP4/ZIP/EXE/GIF 等大文件）  
✅ 首次提交已完成（commit `09f693b`，1738 个文件）  
✅ 仓库大小约 100-150MB（可以正常 push）  

---

## 🔧 Step 1：配置你的 GitHub 身份

在项目目录打开终端（Git Bash），替换成你的真实信息：

```bash
cd "D:/AAA我的文件/PKS_千禧难题_统一解"

git config user.email "你的GitHub邮箱@gmail.com"
git config user.name "你的GitHub用户名"
```

---

## 🔧 Step 2：在 GitHub.com 创建远程仓库

1. 打开 https://github.com/new
2. 仓库名建议：`PKS-Millennium-Project` 或 `PKS_千禧难题_统一解`
3. 描述：`Schauberger mathematical-physics: NS equation regularity proof, bell water turbine design, egg-shaped vortex geometry, and unified polarization principle xy=1`
4. **不要勾选** "Add a README file"（我们已经有了）
5. **不要勾选** ".gitignore"（我们已经有了）
6. 选择 Public（公开）或 Private（私有）
7. 点击 "Create repository"

---

## 🔧 Step 3：关联远程仓库并推送

创建仓库后，GitHub 会显示一串命令。复制并执行这两条：

```bash
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

如果使用 SSH（推荐，不用每次输密码）：

```bash
git remote add origin git@github.com:你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

---

## 🔧 Step 4：推送后配置 GitHub Pages（可选）

如果想把公开信和文档以网页形式展示：

1. 进入仓库 → Settings → Pages
2. Source 选 "Deploy from a branch"
3. Branch 选 `main`，文件夹选 `/ (root)`
4. Save — 几分钟后访问 `https://你的用户名.github.io/仓库名/`

---

## ⚠️ 注意

### 推送前一定确认

```bash
# 查看推送的文件总数
git ls-files | wc -l

# 查看推送到哪个远程仓库
git remote -v
```

### 如果需要修改 gitignore

```bash
# 编辑 .gitignore 文件后
git add .gitignore
git commit -m "Update .gitignore"
git push
```

### 关于大文件

目前 `.gitignore` 排除了：
- 所有 PDF、DOCX、PPTX（参考资料，太占空间）
- 所有 MP4、ZIP、EXE（二进制大文件）
- 所有 GIF（大尺寸动图）
- 所有 MHTML（网页存档）

**重要：这些文件仍然在本地**，只是不上传 GitHub。  
如需分享参考资料，建议用百度网盘/Google Drive。

### 以后每次更新推送

```bash
cd "D:/AAA我的文件/PKS_千禧难题_统一解"
git add .
git commit -m "描述你做了什么改动"
git push
```

---

## 📋 文件状态一览

| 类型 | 本地总数 | 已排除 | 上传数 | 说明 |
|------|:------:|:------:|:------:|------|
| MD 文档 | ~200 | 0 | ~200 | 全部保留 |
| PY 代码 | ~530 | 0 | ~530 | 全部保留 |
| MM 脑图 | ~10 | 0 | ~10 | 全部保留 |
| JSON/其他 | ~50 | 0 | ~50 | 全部保留 |
| JPG/PNG | ~800 | 0 | ~800 | 保留（参考图） |
| PDF/DOCX | >30 | 全部 | 0 | 太大了，不上传 |
| MP4/ZIP/EXE | ~5 | 全部 | 0 | 太大了，不上传 |
| GIF | ~20 | 全部 | 0 | 太大了，不上传 |
| **总计** | **~2276** | **~538** | **1738** | |

---

## 🆘 常见问题

**Q: push 时提示文件超过 100MB？**  
A: 说明有大文件没被 gitignore 拦住。执行：
```bash
find . -type f -size +50M -not -path "./.git/*"
```
然后把找到的文件路径加到 `.gitignore`。

**Q: 怎么修改刚才的提交者信息？**  
A: 已用临时信息提交了首次 commit。如果想改：
```bash
git config user.email "你的真实邮箱"
git config user.name "你的真实名字"
git commit --amend --reset-author
```

**Q: SSH 密钥怎么设置？**  
A: 参考 GitHub 官方指南：https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

> 💡 **推荐仓库名**: `PKS-Millennium-Project`  
> 📝 **推荐描述**: Schauberger mathematical-physics: NS regularity proof, bell water turbine, egg vortex geometry, xy=1 polarization principle. Human-AI collaborative research.
