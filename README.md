# hashcards

一个 **本地优先（local-first）** 的间隔重复学习应用，灵感来自 Anki 和 Mochi。

![hashcards界面](images/example.png)

## 理念（Philosophy）

hashcards 建立在四个核心原则之上：

1. **Unix 哲学** —— 小而美、可组合的工具，围绕文本流工作  
2. **开源精神** —— 透明、可控、可分享  
3. **认知工程** —— 降低摩擦，优化学习与创作流程  
4. **数据主权** —— 你的数据，完全属于你

## 核心特性（Key Features）

![hashcards统计界面](images/end.png)

- 📝 **基于 Markdown 的卡片** —— 你的卡片只是普通的 `.md` 文件  
- 🔍 **内容寻址（Content-addressable）** —— 卡片由内容哈希标识，而非随意的 ID  
- 🧠 **FSRS 调度算法** —— 当前最先进的间隔重复算法  
- ⚡ **极低摩擦** —— 简单语法，键盘驱动的交互体验  
- 🔧 **Git 友好** —— 可追踪修改、分享卡组、协作学习  
- 🎯 **无数据库绑定** —— 卡片是纯文本，调度状态存储在 SQLite 中

## 安装（Installation）

```bash
# 克隆仓库
git clone https://github.com/1998x-stack/interview_hashcards.git
cd interview_hashcards

# 安装依赖
pip install -r requirements.txt

# 安装 interview_hashcards
pip install -e .
````

## 快速开始（Quick Start）

### 1. 创建你的第一个卡组

创建一个目录用于存放卡片，并添加一个 Markdown 文件：

```bash
mkdir Cards
cd Cards
```

创建 `Math.md`：

```markdown
Q: x² 的导数是什么？
A: 2x

Q: 1/x 的不定积分是什么？
A: ln|x| + C

C: 二次方程求根公式是 [x = (-b ± √(b² - 4ac)) / 2a]。

C: 欧拉恒等式：[e^(iπ)] + [1] = [0]。
```

### 2. 开始学习

```bash
hashcards drill ./Cards
```

这会启动一个 Web 界面，地址为 `http://localhost:8000`，你可以在其中复习卡片。

### 3. 使用键盘快捷键

* **Space** —— 显示答案
* **1** —— 重来（Again，< 10 分钟）
* **2** —— 困难（Hard，约为正常间隔的 80%）
* **3** —— 良好（Good，正常间隔）
* **4** —— 简单（Easy，约为正常间隔的 130%）

## 卡片格式（Card Format）

### 问答卡（Question-Answer Cards）

```markdown
Q: 法国的首都是哪里？
A: 巴黎
```

### 填空卡（Cloze Deletion Cards）

```markdown
C: 线粒体是细胞的 [动力工厂]。
```

每一个 `[...]` 都会生成一张独立的卡片，用于测试该填空。

## 项目结构（Project Structure）

```
hashcards/
├── hashcards/
│   ├── __init__.py
│   ├── parser.py          # 解析 Markdown 卡片
│   ├── scheduler.py       # FSRS 调度算法
│   ├── storage.py         # SQLite 数据库管理
│   ├── hasher.py          # 内容寻址哈希
│   ├── cli.py             # 命令行接口
│   └── web/
│       ├── app.py        # Flask 应用
│       └── templates/    # HTML 模板
├── setup.py
├── requirements.txt
└── README.md
```

## CLI 命令（CLI Commands）

```bash
# 开始学习会话
hashcards drill <cards_directory>

# 查看统计信息
hashcards stats <cards_directory>

# 校验卡片语法
hashcards validate <cards_directory>
```

## 高级用法（Advanced Usage）

### Unix 管道魔法（Unix Pipeline Magic）

由于卡片是纯文本，你可以直接使用标准 Unix 工具：

```bash
# 统计卡片总数
grep -c "^Q:" Cards/*.md

# 查找与某个主题相关的卡片
grep -B1 "mitochondria" Cards/*.md

# 列出所有卡组
ls Cards/*.md

# 统计词数
wc -w Cards/*.md
```

### Git 集成（Git Integration）

```bash
# 初始化 Git 仓库
cd Cards
git init

# 记录你的学习历程
git add .
git commit -m "添加了有机化学卡组"

# 分享到 GitHub
git remote add origin https://github.com/1998x-stack/my-cards.git
git push -u origin main
```

### 脚本化生成卡片（Scripted Card Generation）

从结构化数据生成卡片：

```python
import csv

# 从 CSV 生成词汇卡片
with open('vocab.csv') as f:
    reader = csv.DictReader(f)
    with open('Cards/French_Vocab.md', 'w') as out:
        for row in reader:
            out.write(f"Q: '{row['english']}' 的法语是什么？\n")
            out.write(f"A: {row['french']}\n\n")
```

## 设计决策（Design Decisions）

### 为什么卡片不用数据库存储？

传统的闪卡应用通常将所有内容存储在数据库中，这会带来一些问题：

* **厂商锁定** —— 难以迁移或二次处理数据
* **格式不透明** —— 无法使用标准工具处理
* **难以版本控制** —— 不易与 Git 集成
* **不便分享** —— 不能直接发送一个文件

hashcards 通过将卡片存储为 Markdown 文件解决了这些问题。
只有 *调度状态*（每张卡片的复习时间）存放在 SQLite 中——而这些是可随时重建的临时数据。

### 为什么使用内容寻址（Content-addressable）？

卡片由内容哈希标识，而不是数据库 ID，这意味着：

* **自动去重** —— 相同内容 = 相同卡片
* **安全编辑** —— 修改卡片即生成新卡片
* **Git 友好** —— 更容易追踪内容变化
* **无 ID 冲突** —— 合并冲突本质上是内容冲突

### 为什么选择 FSRS 而不是 SM-2？

FSRS（Free Spaced Repetition Scheduler）是当前最先进的间隔重复算法：

* 比 SM-2 有更准确的记忆预测
* 对“遗忘”的卡片处理更好
* 能自适应不同卡片的难度
* 已被现代 Anki 采用

与简单的倍增间隔算法不同，FSRS 建模的是记忆衰减曲线。

## 与其他工具的对比（Comparison）

| 特性    | hashcards   | Anki      | Mochi         |
| ----- | ----------- | --------- | ------------- |
| 卡片格式  | Markdown 文件 | 数据库       | 数据库           |
| 版本控制  | 原生支持 Git    | 需要插件      | 不支持           |
| 调度算法  | FSRS        | FSRS（需插件） | 简单倍率          |
| 语法    | 极简          | 所见即所得     | Markdown + 冗长 |
| 数据所有权 | 完全          | 完全        | 有限制           |
| 学习成本  | 中等          | 高         | 低             |

## 参与贡献（Contributing）

欢迎贡献！本项目遵循以下原则：

* 保持简单
* 尊重 Unix 哲学
* 维护数据主权
* 尽量减少用户摩擦

## 许可证（License）

MIT License —— 详见 LICENSE 文件

## 致谢（Acknowledgments）

* 灵感来自 [Anki](https://apps.ankiweb.net/) 和 [Mochi](https://mochi.cards/)
* FSRS 算法来自 [open-spaced-repetition](https://github.com/open-spaced-repetition)
* 内容寻址卡片的想法来源于 Andy Matuschak 的笔记系统

## 理念（Philosophy）

> “你的闪卡集合很重要。它应该完全属于你——以纯文本形式存储，用 Git 追踪，用任何工具编辑。应用程序只是你数据的一个视图，而不是一座监狱。”

hashcards 为以下人群而设计：

* 重视数据、希望完全掌控自己内容的人
* 喜欢纯文本与 Unix 工具的人
* 想在 Git 中记录学习过程的人
* 欣赏极简、键盘驱动界面的人
* 相信开放网络与数据可迁移性的人