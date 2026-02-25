# MCP-AgentBench

LLM Agent MCP 工具调用能力基准测试 — 覆盖 Filesystem / PostgreSQL / GitHub / Playwright 四大服务，支持多模型对比与训练数据生产。

> 本仓库 Fork 自 [MCPMark](https://github.com/eval-sys/mcpmark)，保留其评测框架核心（pipeline、MCP 服务对接、verify 机制），裁剪为 **7 个自研任务** 的精简版 benchmark，用于展示任务设计范式和评测结果。

---

## 目录

- [任务列表](#任务列表)
- [仓库结构](#仓库结构)
- [环境搭建](#环境搭建)
  - [1. 安装 pixi](#1-安装-pixi)
  - [2. 克隆仓库并安装依赖](#2-克隆仓库并安装依赖)
  - [3. 配置环境变量](#3-配置环境变量)
  - [4. Filesystem 服务环境](#4-filesystem-服务环境)
  - [5. PostgreSQL 服务环境](#5-postgresql-服务环境)
  - [6. GitHub 服务环境](#6-github-服务环境)
  - [7. Playwright 服务环境](#7-playwright-服务环境)
- [运行评测](#运行评测)
- [创建自定义任务](#创建自定义任务)
- [评测结果](#评测结果)
- [常见问题](#常见问题)

---

## 任务列表

| # | Task ID | MCP 服务 | 任务名称 | 难度 | Qwen3 Coder | SOTA 最高 |
|---|---------|----------|---------|------|-------------|-----------|
| 1 | file-1-v1 | Filesystem | 文件清理与归档 | L1 | 3/4 (75%) | Claude/GPT/Gemini 4/4 |
| 2 | file-1-v2 | Filesystem | 文件清理、去重与归档（进阶） | L2 | 1/4 (25%) | Claude/GPT 4/4 |
| 3 | file-1-v3 | Filesystem | 文件清理、去重与归档（高阶） | L3 | 0/4 (0%) | Claude/GPT 4/4 |
| 4 | file-3 | Filesystem | 配置迁移与审计 | L3 | 1/4 (25%) | Claude/GPT/Gemini 4/4 |
| 5 | postgre-1 | PostgreSQL | 客户分析数据管道 | L3 | 3/4 (75%) | Claude 4/4, GLM-5 4/4 |
| 6 | github-1-v3 | GitHub | 仓库健康审计与修复 | L3 | 2/4 (50%) | 全部 1/4 |
| 7 | pw-1-v2 | Playwright | PyPI 依赖链调查 | L3 | 1/4 (25%) | Claude/GPT/Gemini 4/4 |

SOTA 对比模型：Claude Opus 4.6 / GPT 5.2 / Gemini 3 Pro / GLM-5

---

## 仓库结构

```
mcpmark/
├── pipeline.py                 # 评测主入口
├── pyproject.toml              # 项目配置 + pixi 依赖声明
├── pixi.lock                   # 依赖锁文件
├── .mcp_env.example            # 环境变量模板（复制为 .mcp_env 后填入实际值）
├── Dockerfile                  # GitHub 任务所需 Docker 镜像
├── build-docker.sh             # Docker 构建脚本
├── run-benchmark.sh            # 批量运行脚本
├── run-task.sh                 # 单任务运行脚本
│
├── src/                        # 框架核心代码
│   ├── agents/                 # Agent 执行引擎（MCPMarkAgent / ReAct Agent）
│   ├── mcp_services/           # 4 个 MCP 服务实现
│   │   ├── filesystem/         #   Filesystem 服务
│   │   ├── postgres/           #   PostgreSQL 服务
│   │   ├── github/             #   GitHub 服务
│   │   └── playwright/         #   Playwright 服务
│   ├── aggregators/            # 结果聚合工具
│   ├── base/                   # 服务基类
│   ├── config/                 # 配置 schema
│   ├── model_config.py         # 模型配置（LiteLLM 适配）
│   ├── services.py             # MCP 服务注册表
│   ├── evaluator.py            # 评测器（调用 verify.py）
│   └── ...
│
├── tasks/                      # 评测任务
│   ├── filesystem/standard/    # 4 个 Filesystem 任务
│   │   ├── file_management/file_cleanup_archive/
│   │   ├── file_management_v2/file_cleanup_dedup_archive/
│   │   ├── file_management_v3/file_cleanup_dedup_archive_v3/
│   │   └── config_migration/config_migration_audit/
│   ├── postgres/standard/      # 1 个 PostgreSQL 任务
│   │   └── chinook/customer_analytics_pipeline/
│   ├── github/standard/        # 1 个 GitHub 任务
│   │   └── mcpmark-cicd/repository_health_audit_v3/
│   └── playwright/standard/    # 1 个 Playwright 任务
│       └── web_investigation/pypi_dependency_chain/
│
├── test_environments/          # Filesystem 任务的初始测试文件
│   ├── file_management/        # → file-1-v1 的初始文件
│   ├── file_management_v2/     # → file-1-v2 的初始文件
│   ├── file_management_v3/     # → file-1-v3 的初始文件
│   └── config_migration/       # → file-3 的初始文件
├── github_state/               # GitHub 任务的仓库初始状态快照
└── postgres_state/             # PostgreSQL 备份文件（框架自动下载）
```

---

## 环境搭建

### 1. 安装 pixi

[pixi](https://pixi.sh/) 是本项目的包管理器，它基于 `pyproject.toml` 管理 Python 依赖和虚拟环境。

#### Linux / macOS

```bash
curl -fsSL https://pixi.sh/install.sh | bash

# 使环境变量生效
source ~/.bashrc      # Linux
source ~/.zshrc       # macOS (zsh)
```

#### Windows

```powershell
irm https://pixi.sh/install.ps1 | iex
```

安装完后**重启终端**（PowerShell / CMD），验证：

```powershell
pixi --version
```

> **Windows 特别说明**：Python 在 Windows 上默认使用 GBK 编码读取文件，会导致含中文注释的 `meta.json` 加载失败。需要设置以下环境变量（建议永久写入系统变量）：
>
> ```powershell
> # 永久写入（推荐）
> [System.Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
> # 重启终端后生效
>
> # 或仅当前会话临时设置（CMD 用 set PYTHONUTF8=1）
> $env:PYTHONUTF8 = "1"
> ```

#### pixi 是怎么管理环境的

- 项目依赖声明在 `pyproject.toml` 的 `[project] dependencies` 中
- `pixi.lock` 锁定了所有依赖的精确版本，确保团队环境一致
- `pixi install` 会在项目根目录下创建 `.pixi/` 虚拟环境
- **所有 Python 命令都通过 `pixi run` 执行**，它会自动激活虚拟环境
- `.pixi/` 目录已在 `.gitignore` 中排除，不会被提交
- 如果环境损坏，删除 `.pixi/` 后重新 `pixi install` 即可

```bash
pixi run python -m pipeline --help    # 通过 pixi 执行 Python
pixi run python -c "import litellm"   # 验证依赖是否安装
pixi shell                            # 进入 pixi 虚拟环境的交互 shell
```

> **注意**：`pixi run` 必须在仓库根目录（包含 `pyproject.toml` 的目录）下执行，否则会报 `could not find pixi.toml`。

---

### 2. 克隆仓库并安装依赖

```bash
git clone https://github.com/tanteijms/mcpmark.git
cd mcpmark
pixi install
```

`pixi install` 会自动：
- 创建 Python 虚拟环境（`.pixi/`）
- 安装 `pyproject.toml` 中声明的所有依赖（litellm、openai、psycopg2、playwright 等）

---

### 3. 配置环境变量

```bash
cp .mcp_env.example .mcp_env
```

Windows PowerShell:

```powershell
Copy-Item .mcp_env.example .mcp_env
```

然后编辑 `.mcp_env`，填入你的实际 API Key 和服务配置。各字段说明见 [`.mcp_env.example`](.mcp_env.example)。

> **安全提醒**：`.mcp_env` 含敏感密钥，已在 `.gitignore` 中排除，不会被提交到仓库。

---

### 4. Filesystem 服务环境

**零配置**，开箱即用。

Filesystem 任务操作的是本地文件系统。框架运行时会将 `test_environments/{category_id}/` 下的初始文件复制到临时目录，模型在临时目录中执行操作，`verify.py` 检查结果。

`.mcp_env` 中只需确认一行：

```bash
FILESYSTEM_TEST_ROOT="./test_environments"
```

无需安装任何额外软件。支持 Linux / macOS / Windows。

---

### 5. PostgreSQL 服务环境

PostgreSQL 任务需要一个运行中的 PostgreSQL 实例，框架会**自动从 CDN 下载 Chinook 数据库备份并恢复**。

#### 方案 A：Docker 运行（推荐，全平台通用）

```bash
# 启动 PostgreSQL 容器
docker run -d \
  --name mcpmark-postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:16

# 验证连接
docker exec mcpmark-postgres psql -U postgres -c "SELECT version();"
```

> **Windows Docker 拉取失败？** 国内访问 Docker Hub 可能超时。解决方案：
> 1. 打开 Docker Desktop → ⚙️ → **Docker Engine**，添加镜像源后 Apply & restart：
> ```json
> {
>   "registry-mirrors": [
>     "https://mirrors.aliyun.com",
>     "https://mirror.ccs.tencentyun.com",
>     "https://docker.mirrors.tuna.tsinghua.edu.cn"
>   ]
> }
> ```
> 2. 如果镜像源仍失败，在 Docker Desktop → ⚙️ → **Proxies** 中配置 Clash 代理（HTTP/HTTPS 均填 `http://127.0.0.1:7890`），Apply & restart 后重试。

框架运行时需要本地有 `pg_restore` 命令来恢复数据库备份。Docker 容器里有，但框架是在宿主机上通过 subprocess 调用的，所以**宿主机也需要安装 PostgreSQL 客户端工具**：

**Linux:**

```bash
sudo apt-get install -y postgresql-client
```

**macOS:**

```bash
brew install libpq
echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Windows:**

从 https://www.postgresql.org/download/windows/ 下载安装包，安装时**只勾选 Command Line Tools**，安装完成后把以下路径加入系统 PATH（版本号按实际调整）：

```
C:\Program Files\PostgreSQL\16\bin
```

验证（需重启终端）：

```powershell
pg_restore --version
```

#### 方案 B：本地安装 PostgreSQL

**Linux:**

```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'password';"
```

**macOS:**

```bash
brew install postgresql@16
brew services start postgresql@16
```

**Windows:**

从 https://www.postgresql.org/download/windows/ 下载完整安装包，安装时包含服务端。

#### .mcp_env 配置

```bash
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_USERNAME="postgres"
POSTGRES_PASSWORD="password"
```

> **注意**：框架首次运行 PostgreSQL 任务时，会自动从 `https://storage.mcpmark.ai/postgres/chinook.backup` 下载备份文件到 `postgres_state/` 目录，然后用 `pg_restore` 恢复到本地 PostgreSQL。无需手动导入数据库。

---

### 6. GitHub 服务环境

GitHub 任务需要 **Docker** + **GitHub Personal Access Token (PAT)**。

#### 6.1 Docker

GitHub MCP 服务器运行在 Docker 容器中。确保 Docker 已安装并运行：

```bash
docker --version
```

**Linux:**

```bash
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER   # 免 sudo，需重新登录生效
```

**macOS / Windows:**

安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 并启动。

#### 6.2 构建 MCPMark Docker 镜像

构建前需要先拉取基础镜像（国内网络建议先确保 Docker 代理或镜像源已配置好）：

```bash
# 先拉基础镜像（如果之前 Docker Hub 拉取失败过，先确认网络通畅）
docker pull python:3.12-slim
docker pull postgres:16
```

然后构建（预计 10-15 分钟）：

```bash
# Linux / macOS
chmod +x build-docker.sh
./build-docker.sh

# Windows PowerShell / CMD
docker build -t evalsysorg/mcpmark:latest .
```

构建完成后验证：

```bash
docker images evalsysorg/mcpmark
```

> **注意**：GitHub 任务会创建临时私有仓库进行评测，评测结束后自动删除。必须使用私有仓库，否则模板中的 `@username` mention 会骚扰原始仓库作者。本项目已默认强制 `private=True`。

#### 6.3 GitHub PAT

创建一个 Personal Access Token：

1. 前往 https://github.com/settings/tokens → **Generate new token (classic)**
2. 勾选以下权限（缺任一项会导致对应步骤失败）：
   - `repo`（Full control）— 创建/删除仓库、push 代码
   - `workflow` — push 含 `.github/workflows/` 的代码（**必须勾选，否则会报 `refusing to allow a PAT to create or update workflow`**）
   - `admin:org`（如果使用组织账号）
3. 复制生成的 token

#### 6.4 GitHub 评测组织

评测时框架会在指定的 GitHub 组织下创建临时私有仓库（跑完后清理）。你需要：

1. 创建或使用一个 GitHub Organization
2. 确保你的 PAT 对该组织有创建仓库的权限

#### 6.5 .mcp_env 配置

```bash
GITHUB_TOKENS="github_pat_xxxxxxxxxxxx"
GITHUB_EVAL_ORG="your-org-name"
```

> **注意**：`github_state/` 目录包含仓库初始状态快照（issues、PRs、代码），框架运行时会自动将其导入到临时测试仓库。

---

### 7. Playwright 服务环境

Playwright 任务使用浏览器访问网页并提取信息，需要安装 Chromium 浏览器。

#### 安装浏览器

**推荐通过 pixi 安装**（使用项目内置的 playwright 版本，避免版本冲突）：

```bash
# Linux / macOS
pixi run python -m playwright install chromium
pixi run python -m playwright install-deps chromium   # Linux 需要

# Windows PowerShell
pixi run python -m playwright install chromium
```

> **Windows 下载超时？** Chromium 浏览器从 Google 服务器下载，国内可能超时。设置代理后重试：
>
> ```powershell
> $env:HTTPS_PROXY = "http://127.0.0.1:7890"
> pixi run python -m playwright install chromium
> ```

#### .mcp_env 配置

```bash
PLAYWRIGHT_BROWSER="chromium"
PLAYWRIGHT_HEADLESS="True"
```

`PLAYWRIGHT_HEADLESS="True"` 表示无头模式运行（服务器环境必须）。本地调试可改为 `"False"` 看到浏览器界面。

---

## 运行评测

### 基本命令

```bash
pixi run python -m pipeline \
  --exp-name <实验名> \
  --mcp <mcp服务> \
  --tasks <category_id/task_id> \
  --models <模型名> \
  --k <重复轮次>
```

Windows PowerShell 中用反引号 `` ` `` 换行：

```powershell
pixi run python -m pipeline `
  --exp-name <实验名> `
  --mcp <mcp服务> `
  --tasks <category_id/task_id> `
  --models <模型名> `
  --k <重复轮次>
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--exp-name` | 实验名称（决定结果目录名） | `exp-filesystem-001` |
| `--mcp` | MCP 服务类型 | `filesystem` / `postgres` / `github` / `playwright` |
| `--tasks` | 任务路径 (category_id/task_id) | `file_management/file_cleanup_archive` |
| `--models` | 模型名（见下方表格） | `or-qwen3-coder` |
| `--k` | 独立运行轮次（推荐 4） | `4` |

### 可用模型

在 `src/model_config.py` 中配置，底层使用 [LiteLLM](https://docs.litellm.ai/) 适配多个 Provider。

| `--models` 参数 | 实际模型 | Provider |
|-----------------|---------|----------|
| `or-qwen3-coder` | Qwen3 Coder | OpenRouter |
| `or-claude-opus-4.6` | Claude Opus 4.6 | OpenRouter |
| `or-gpt-5.2` | GPT 5.2 | OpenRouter |
| `or-gemini-3-pro` | Gemini 3 Pro | OpenRouter |
| `or-glm-5` | GLM-5 | OpenRouter |
| `doubao-seed-2-pro` | Doubao Seed 2.0 Pro | 火山方舟 |

添加新模型：在 `model_config.py` 的 `MODEL_CONFIGS` 字典中添加条目，指定 `provider`、`api_key_var`、`litellm_input_model_name`，并在 `.mcp_env` 中配置对应的 API Key。

### 所有 7 个任务的运行命令

```bash
# === Filesystem（4 个任务，无需外部服务） ===
pixi run python -m pipeline --exp-name exp --mcp filesystem --tasks file_management/file_cleanup_archive --models or-qwen3-coder --k 4
pixi run python -m pipeline --exp-name exp --mcp filesystem --tasks file_management_v2/file_cleanup_dedup_archive --models or-qwen3-coder --k 4
pixi run python -m pipeline --exp-name exp --mcp filesystem --tasks file_management_v3/file_cleanup_dedup_archive_v3 --models or-qwen3-coder --k 4
pixi run python -m pipeline --exp-name exp --mcp filesystem --tasks config_migration/config_migration_audit --models or-qwen3-coder --k 4

# === PostgreSQL（需要 PG 服务 + pg_restore） ===
pixi run python -m pipeline --exp-name exp --mcp postgres --tasks chinook/customer_analytics_pipeline --models or-qwen3-coder --k 4

# === GitHub（需要 Docker + PAT） ===
pixi run python -m pipeline --exp-name exp --mcp github --tasks mcpmark-cicd/repository_health_audit_v3 --models or-qwen3-coder --k 4

# === Playwright（需要 Chromium） ===
pixi run python -m pipeline --exp-name exp --mcp playwright --tasks web_investigation/pypi_dependency_chain --models or-qwen3-coder --k 4
```

### 后台运行（Linux / macOS，防止 SSH 断开杀进程）

```bash
mkdir -p log
nohup pixi run python -m pipeline \
  --exp-name exp --mcp filesystem \
  --tasks file_management/file_cleanup_archive \
  --models or-qwen3-coder --k 4 \
  > log/run.log 2>&1 &
```

### 多任务串行运行

**不能**用逗号分隔 `--tasks`，必须分开跑：

```bash
# ❌ 错误 — 会报 0/0 tasks
--tasks category_a/task1,category_b/task2

# ✅ 正确 — 用 && 串联
pixi run python -m pipeline --exp-name exp --mcp filesystem --tasks file_management/file_cleanup_archive --models or-qwen3-coder --k 4 && \
pixi run python -m pipeline --exp-name exp --mcp filesystem --tasks file_management_v2/file_cleanup_dedup_archive --models or-qwen3-coder --k 4
```

### 结果目录

```
results/{exp-name}/{model}__{mcp}/run-{n}/
├── summary.json                          # 本轮汇总
└── {category_id}__{task_id}/
    ├── messages.json                     # 完整对话记录（可作 SFT 训练数据）
    ├── trajectory.json                   # 操作轨迹
    └── summary.json                      # 任务级汇总（含 pass/fail）
```

### 聚合多轮结果

```bash
pixi run python -m src.aggregators.aggregate_results --exp-name exp
```

---

## 创建自定义任务

### 任务三件套

每个任务由 3 个必需文件组成，放在 `tasks/{mcp}/standard/{category_id}/{task_id}/` 目录下：

| 文件 | 说明 |
|------|------|
| `description.md` | 给模型看的任务指令（含操作步骤和输出格式要求） |
| `meta.json` | 任务元数据（task_id, difficulty, mcp, tags 等） |
| `verify.py` | 验证脚本，`exit(0)` 通过 / `exit(1)` 失败 |
| `initial_state/` | 初始测试文件（仅 Filesystem 任务需要） |
| `label.txt` | 标准答案（仅 Playwright 任务需要） |

### description.md — 任务描述

给模型看的指令，要求清晰、具体、可执行：

```markdown
# 任务标题

## 任务要求
1. 第一步：做什么...
2. 第二步：做什么...

## 输出格式
（明确告诉模型输出什么格式，verify.py 依赖它来验证）

## 注意事项
- 关键约束条件
```

**设计要点**：步骤越具体模型越容易完成（降低难度），模糊描述会提高失败率（提高难度）。

### meta.json — 任务元数据

```json
{
  "task_id": "my_custom_task",
  "task_name": "My Custom Task",
  "category_id": "my_category",
  "category_name": "My Category",
  "description": "一句话描述任务",
  "author": "your_name",
  "created_at": "2026-01-01",
  "difficulty": "L2",
  "tags": ["data extraction"],
  "mcp": ["filesystem"],
  "meta_data": {
    "stateType": null,
    "stateContent": null,
    "stateUrl": null,
    "stateOriginalUrl": null
  }
}
```

**关键注意事项**：

| 字段 | 规则 | 踩坑点 |
|------|------|--------|
| `task_id` | 必须与目录名一致 | 不一致会导致 `0/0 tasks` |
| `category_id` | 必须全局唯一 | 与其他任务冲突会导致 initial_state 互相覆盖 |
| `mcp` | 必须与 `--mcp` 参数匹配 | 数组格式 `["filesystem"]` |
| `difficulty` | L1 / L2 / L3 | 简单 / 中等 / 困难 |

### verify.py — 验证脚本

返回 `exit(0)` 通过，`exit(1)` 失败。不同 MCP 服务验证方式不同：

| MCP 服务 | 验证对象 | 读取方式 |
|----------|---------|---------|
| Filesystem | 文件系统中的文件/目录 | 读取 `FILESYSTEM_TEST_ROOT/{category_id}/` |
| PostgreSQL | 数据库中的表/视图/函数 | `psycopg2` 连接数据库查询 |
| GitHub | 仓库的 issue/PR/label | GitHub API（`MCP_GITHUB_TOKEN` 环境变量） |
| Playwright | 模型的文本输出 | 读取 `MCP_MESSAGES` 指向的 `messages.json` |

**Filesystem verify.py 模板**：

```python
#!/usr/bin/env python3
import sys, os

def verify():
    base = os.environ.get("FILESYSTEM_TEST_ROOT", "./test_environments")
    root = os.path.join(base, "my_category")

    passed = 0
    total = 2

    # Step 1: 检查文件
    if os.path.exists(os.path.join(root, "expected_file.txt")):
        print("| Step 1: expected_file.txt exists ✓")
        passed += 1
    else:
        print("| Step 1: expected_file.txt NOT found ✗")

    # Step 2: 检查内容
    # ...

    print(f"\nScore: {passed}/{total}")
    print("TASK PASSED" if passed == total else "TASK FAILED")
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
```

**PostgreSQL verify.py 要点**：

```python
import psycopg2, os

def get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ.get("POSTGRES_USERNAME", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
        dbname="your_database"
    )

conn = get_conn()
conn.autocommit = True   # 重要！否则一个 step 报错会导致后续全部级联失败
```

**Playwright verify.py 要点**：

```python
import json, os

messages_path = os.getenv("MCP_MESSAGES")
with open(messages_path) as f:
    messages = json.load(f)

# 从最后一条 assistant 消息中提取模型输出
for msg in reversed(messages):
    if msg.get("role") == "assistant":
        content = msg.get("content", [])
        # 解析 content 中的 text，匹配 <answer> 标签等...
        break
```

### 部署任务到框架

#### 步骤 1：创建任务目录

路径格式：`tasks/{mcp}/standard/{category_id}/{task_id}/`

```bash
# 以 Filesystem 任务为例
mkdir -p tasks/filesystem/standard/my_category/my_custom_task
```

#### 步骤 2：放入任务文件

```bash
cp description.md meta.json verify.py \
   tasks/filesystem/standard/my_category/my_custom_task/
```

#### 步骤 3：部署初始状态（仅 Filesystem 任务需要）

**这是最容易出错的地方！** Filesystem 任务的初始文件需要放到 **两个位置**：

**位置 1** — 任务目录下（存档）：

```
tasks/filesystem/standard/my_category/my_custom_task/
├── description.md
├── meta.json
├── verify.py
└── initial_state/          ← 存档用
    ├── file1.txt
    └── subdir/
        └── file2.dat
```

**位置 2** — `test_environments/`（运行时实际读取）：

```
test_environments/my_category/     ← 框架运行时从这里复制
├── file1.txt
└── subdir/
    └── file2.dat
```

**注意**：`test_environments/{category_id}/` 下放的是 `initial_state/` 的**内容**，不是整个 `initial_state` 目录：

```bash
# ✅ 正确
mkdir -p test_environments/my_category
cp -r tasks/filesystem/standard/my_category/my_custom_task/initial_state/* \
      test_environments/my_category/

# ❌ 错误（会多一层 initial_state 目录）
cp -r .../initial_state test_environments/my_category/
```

**运行时流程**：

```
meta.json 中 "category_id": "my_category"
     ↓
框架复制 test_environments/my_category/ → 临时工作目录
     ↓
模型在临时工作目录中操作文件
     ↓
verify.py 检查临时工作目录中的结果
```

> **如果两个任务的 category_id 相同，它们会共享 initial_state，互相干扰！** 建议使用独特前缀。

#### 步骤 4（仅 PostgreSQL / GitHub / Playwright）

- **PostgreSQL**：不需要 initial_state。框架自动从 Chinook 数据库模板创建临时数据库。
- **GitHub**：仓库初始状态放在 `github_state/` 目录，框架自动导入。
- **Playwright**：不需要 initial_state，Playwright 任务操作的是公开网页。需要 `label.txt` 存放标准答案。

#### 步骤 5：验证部署

```bash
# 运行任务（k=1 快速验证）
pixi run python -m pipeline \
  --exp-name test \
  --mcp filesystem \
  --tasks my_category/my_custom_task \
  --models or-qwen3-coder \
  --k 1
```

如果看到 `Tasks passed: 0/0`，检查 `meta.json` 中的 `category_id` 和 `task_id` 是否与目录结构一致。

---

## 评测结果

### Qwen3 Coder vs SOTA 对比（k=4）

| 任务 | Qwen3 Coder | Claude Opus 4.6 | GPT 5.2 | Gemini 3 Pro | GLM-5 |
|------|-------------|-----------------|---------|-------------|-------|
| file-1-v1 文件清理归档 | **3/4** | 4/4 | 4/4 | 4/4 | 3/4 |
| file-1-v2 去重归档（进阶） | 1/4 | **4/4** | **4/4** | 2/4 | 4/4 |
| file-1-v3 去重归档（高阶） | 0/4 | **4/4** | **4/4** | 3/4 | 2/4 |
| file-3 配置迁移审计 | 1/4 | **4/4** | **4/4** | **4/4** | 3/4 |
| postgre-1 客户分析管道 | **3/4** | **4/4** | 0/4 | 0/4 | **4/4** |
| github-1-v3 仓库健康审计 | **2/4** | 1/4 | 1/4 | 1/4 | 1/4 |
| pw-1-v2 PyPI 依赖链 | 1/4 | **4/4** | **4/4** | **4/4** | 4/4 |

### Qwen3 Coder 通过率梯度

```
file-1-v1 (75%) = postgre-1 (75%) > github-v3 (50%) > file-1-v2 (25%) = file-3 (25%) = pw-1-v2 (25%) > file-1-v3 (0%)
```

### 训练数据产出（7 任务 × Qwen3 Coder × 4 轮）

| 类型 | 数量 |
|------|------|
| 成功 trajectory (SFT 正样本) | 11 条 |
| 失败 trajectory (RL 负样本) | 17 条 |
| 合计 | 28 条 |

---

## 常见问题

### 环境相关

| 问题 | 原因 & 解决 |
|------|------------|
| `pixi: command not found` | 安装后需重启终端。Linux: `source ~/.bashrc`，macOS: `source ~/.zshrc` |
| `could not find pixi.toml` | 必须在仓库根目录（含 `pyproject.toml`）下执行 `pixi run` |
| `pg_restore: command not found` | 需安装 PostgreSQL 客户端工具（见上方 PostgreSQL 环境搭建） |
| Playwright 浏览器下载超时 | 设代理：`$env:HTTPS_PROXY="http://127.0.0.1:7890"`，再执行 `pixi run python -m playwright install chromium` |
| Docker 拉取镜像超时（国内） | Docker Engine 中配置镜像源（阿里/腾讯），或在 Proxies 中填入 Clash 代理地址 |
| Docker 镜像构建失败 | 确认 Docker Desktop 已启动且基础镜像已拉取（`docker pull python:3.12-slim`） |
| **[Windows]** `meta.json` GBK 编码错误 | 设置 `PYTHONUTF8=1`，建议永久写入：`[System.Environment]::SetEnvironmentVariable("PYTHONUTF8","1","User")` |
| **[Windows]** CMD 中无法执行 `$env:` | CMD 用 `set PYTHONUTF8=1`，PowerShell 用 `$env:PYTHONUTF8="1"` |

### 任务运行相关

| 问题 | 原因 & 解决 |
|------|------------|
| `Tasks passed: 0/0` | `--tasks` 路径不对，检查 `meta.json` 中的 `category_id/task_id` 是否与目录一致 |
| Filesystem 初始文件找不到 | `test_environments/{category_id}/` 目录不存在或为空 |
| PostgreSQL `current transaction is aborted` | verify.py 中需设置 `conn.autocommit = True` |
| GitHub `Cannot import template to a public repository` | 已在框架中修复（强制 `private=True`），无需手动处理 |
| GitHub `refusing to allow a PAT to create workflow without workflow scope` | PAT 缺少 `workflow` 权限，去 https://github.com/settings/tokens 编辑 token 勾选 `workflow` |
| GitHub verify.py 读不到 Token | 框架传的环境变量名是 `MCP_GITHUB_TOKEN`，不是 `GITHUB_TOKEN` |
| SSH 断开进程被杀 | 使用 `nohup ... > log/run.log 2>&1 &` 后台运行 |

---

## 致谢

本项目基于 [MCPMark](https://github.com/eval-sys/mcpmark) 框架构建。MCPMark 是一个全面的 MCP 压力测试基准，用于评估模型和 Agent 在真实 MCP 场景中的能力。

```bibtex
@misc{wu2025mcpmark,
      title={MCPMark: A Benchmark for Stress-Testing Realistic and Comprehensive MCP Use},
      author={Zijian Wu and Xiangyan Liu and Xinyuan Zhang and Lingjun Chen and Fanqing Meng
              and Lingxiao Du and Yiran Zhao and Fanshi Zhang and Yaoqi Ye and Jiawei Wang
              and Zirui Wang and Jinjie Ni and Yufan Yang and Arvin Xu and Michael Qizhe Shieh},
      year={2025},
      eprint={2509.24002},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2509.24002},
}
```

## License

Apache License 2.0 — 详见 [LICENSE](LICENSE)。
