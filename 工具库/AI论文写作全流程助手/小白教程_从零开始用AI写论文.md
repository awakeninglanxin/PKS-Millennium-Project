# 小白教程：从零开始用 AI 写论文

> 🎯 **目标**：30 分钟内，让完全没用过 AI 的小白也能开始用 AI 辅助论文写作
> 📖 这是给**第一次接触** Claude Code / Codex 的人看的。如果你已经会用了，跳到 `论文写作Prompt模板库.md`

---

## 第 0 步：先搞懂的 3 个概念（1 分钟速通）

| 名词 | 一句话理解 | 类比 |
|------|-----------|------|
| **AI 对话** | 你打字，AI 回复 | 和微信聊天一样 |
| **Skills** | 把一段很长的指令"固定下来"变成一个按钮 | Word 里的"字体→微软雅黑"快捷键 |
| **Codex / Claude Code** | 能在你电脑上读写文件的 AI | 一个能操作你电脑的数字实习生 |

**Skill 是什么？为什么需要它？**

想象你每次润色论文摘要都要打："你现在是一个资深的英语润色专家，请帮我修改这段摘要，要求符合学术规范，用词精准，句式多样，保持被动语态...balabala"。每次都要打一遍，很烦。

**Skills 就是把这串话提前写好**。你安装 `nature-polish` 之后，只需要说 `/nature-polish`，AI 就自动加载了"资深润色专家"的设定。再也不用重复打那段话。

---

## 第 1 步：选一个 AI 助手装好（5 分钟）

### 方案 A：Claude Code（推荐，科研社区生态最丰富）

```bash
# 在终端执行（需要 Node.js）
npm install -g @anthropic-ai/claude-code

# 启动
claude
```

第一次使用会要你登录 Anthropic 账号。

### 方案 B：OpenAI Codex（推荐新手，有桌面 App）

```
1. 打开 https://openai.com/codex/
2. 下载对应你的系统（Mac/Windows）
3. 安装后打开，用 ChatGPT 账号登录
```

推荐优先用桌面 App（有可视化界面，新手友好）。

### 方案 C：ChatGPT 网页版（零门槛）

```
直接打开 https://chat.openai.com
把 Prompt 复制粘贴进去
```

> 💡 用方案 C 也可以，但没法用 Skills（Skill 需要 Codex 或 Claude Code）。

---

## 第 2 步：安装第一个 Skill 试试（10 分钟）

**用 Claude Code 的：**

打开终端，输入 `claude`，然后在对话中粘贴：

```
安装这个skill，skill项目地址为：https://github.com/Yuan1z0825/nature-skills
```

AI 会自动帮你下载、解压、放好。装完后说 `/nature-polish` 测试一下。

**用 Codex 的：**

在 Codex 对话中粘贴：

```
/plugin marketplace add Yuan1z0825/nature-skills
/plugin install nature-skills
```

**用 ChatGPT 网页的：**

把我们的 Prompt 模板直接复制到对话框就行（虽然无法安装 Skills，但能用 Prompt）。

---

## 第 3 步：打开我们的 Python 工具

```bash
# 下载并进入目录
cd AI论文写作全流程助手/

# 运行（Python 3.8+）
python paper_ai_assistant.py
```

会看到一个菜单：

```
  🔍  [topic      ]  选题与开题
  📚  [lit-review  ]  文献综述
  ⚙️  [method     ]  方法论设计
  🧪  [experiment ]  实验与数据分析
  ✍️  [writing    ]  论文撰写
  📊  [figures    ]  图表与可视化
  ✨  [polish     ]  润色与自查
  📤  [submit     ]  投稿与返修
```

选你当前的阶段（比如 `lit-review`），工具会给你三样东西：

1. 推荐装哪个 Skill
2. 一段 Prompt（复制到 AI 对话框）
3. 这段阶段最容易踩的坑

---

## 第 4 步：把你的论文喂给 AI（实战）

假设你现在在写文献综述：

### 4.1 在 Python 工具里选 `lit-review`

### 4.2 复制 Prompt 到 Claude Code / Codex / ChatGPT

### 4.3 粘贴后，补充你的具体信息：

```
请帮我系统性地综述 [基于深度学习的医学影像分割] 的相关文献。

要求：
1. 按时间线/方法线/结论线三维度组织
2. ...（后面的保持原样）
```

### 4.4 AI 会输出文献综述的初稿

### 4.5 关键！检查 AI 的输出：

- ✅ 每个引用是否真实存在？（用 DOI 查）
- ✅ 逻辑线是否合理？
- ✅ 有没有遗漏重要的论文？

---

## 第 5 步：四个"别"（最容易被坑的地方）

| 别做的事 | 为什么 |
|----------|--------|
| **别让 AI 写完整篇论文** | AI 写的论文"味太冲"，审稿人一眼能看出来 |
| **别不验证引用** | AI 会编造不存在的论文（幻觉），每条引用必须用 DOI 查 |
| **别一上来开 Full Access** | Codex 的完全访问权限会让 AI 无确认删改你的文件 |
| **别在桌面写论文** | 把项目放在专门的文件夹（`~/papers/paper-xxx/`），不然 AI 生成的文件到处飞 |

---

## 常见问题

**Q: AI 润色后的论文，查重能过吗？**

A: AI 润色 ≠ 抄袭。但如果你整段把 AI 生成的文字原样放进去，可能会被检测。建议：把 AI 输出当"建议"，用你自己的语言重写一遍。

**Q: 投稿期刊会不会查 AI 使用？**

A: Nature 等期刊允许用 AI 辅助写作，但需要声明。我们的 Skills 就是为了帮你**更规范地**使用 AI。

**Q: 我的电脑跑得动吗？**

A: Claude Code / Codex 是云端的，你的电脑只是个"聊天框"，不需要 GPU，任何笔记本都能跑。

**Q: 这些要钱吗？**

A: Claude Code 和 Codex 都有免费额度（有限）。Skills 是开源免费的。ChatGPT 网页版有免费版（功能受限）。

---

## 下一步

- 熟练后看 `论文写作Prompt模板库.md`（当词典查）
- 想装更多工具看 `Skills工具安装速查手册.md`
- 担心学术规范看 `学术诚信与避坑指南.md`
