# MCPMark 自定义任务快速上手指南

> 本文档面向数据生产团队，指导如何基于 MCPMark 框架设计、部署和运行自定义评测任务。
> 基于实际踩坑经验总结，涵盖 Filesystem / PostgreSQL / GitHub / Playwright 四种 MCP 服务。

---

## 一、环境准备

### 1.1 基础环境

```bash
# Ubuntu 22.04 服务器
apt-get update && apt-get install -y build-essential curl git libpq-dev docker.io zip

# 安装 pixi（Python 环境管理）
curl -fsSL https://pixi.sh/install.sh | bash
source ~/.bashrc

# 启动 Docker（GitHub 任务需要）
systemctl start docker
```

### 1.2 MCPMark 仓库

```bash
git clone <mcpmark-repo-url> MCPMark
cd MCPMark/mcpmark
pixi install  # 安装所有依赖
```

### 1.3 环境变量配置

编辑 `MCPMark/mcpmark/.mcp_env`：

```bash
# [必填] OpenRouter API Key（统一调用各模型）
OPENROUTER_API_KEY="sk-or-v1-xxxxxxxxxxxxxxxx"

# [Filesystem 任务]
FILESYSTEM_TEST_ROOT="./test_environments"

# [Playwright 任务]
PLAYWRIGHT_BROWSER="chromium"
PLAYWRIGHT_HEADLESS="True"

# [PostgreSQL 任务] — 需要本地运行 PostgreSQL
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_USERNAME="postgres"
POSTGRES_PASSWORD="your_password"

# [GitHub 任务] — 需要 GitHub PAT + Docker
GITHUB_TOKENS="github_pat_xxxxxxxxxx"
GITHUB_EVAL_ORG="your-org-name"
```

### 1.4 Playwright 浏览器安装

```bash
npx -y playwright install chromium
npx -y playwright install-deps chromium
```

### 1.5 可用模型

在 `src/model_config.py` 中配置 OpenRouter 模型，示例：

| 模型名（--models 参数） | 实际模型 |
|--------------------------|----------|
| `or-claude-opus-4.6` | Claude Opus 4.6 |
| `or-gpt-5.2` | GPT 5.2 |
| `or-gemini-3-pro` | Gemini 3 Pro |
| `or-qwen3-coder` | Qwen3 Coder |

可根据需要在 `model_config.py` 中添加新模型。

---

## 二、任务目录结构

### 2.1 数据目录（设计 & 存档）

建议按 MCP 服务类型分目录管理自定义任务：

```
your_data_dir/
├── filesystem/          # Filesystem 类任务
│   ├── task-1/
│   │   ├── description.md
│   │   ├── meta.json
│   │   ├── verify.py
│   │   └── initial_state/    # 初始文件（Filesystem 专用）
│   └── task-2/
├── postgresql/
│   └── pg-task-1/
├── github/
│   └── gh-task-1/
└── playwright/
    └── pw-task-1/
```

### 2.2 MCPMark 框架任务目录（部署运行）

```
MCPMark/mcpmark/tasks/
├── filesystem/standard/{category_id}/{task_id}/
├── postgres/standard/{category_id}/{task_id}/
├── github/standard/{category_id}/{task_id}/
└── playwright/standard/{category_id}/{task_id}/
```

**关键路径规则**：`tasks/{mcp_service}/standard/{category_id}/{task_id}/`

---

## 三、任务三件套

每个任务必须包含 3 个文件：

### 3.1 description.md — 任务描述

给模型看的指令，要求清晰、具体、可执行。

```markdown
# 任务标题

## 任务要求
1. 第一步...
2. 第二步...

## 输出格式
（明确告诉模型输出什么格式）

## 注意事项
- 关键约束条件
```

**设计要点**：
- 步骤越具体，模型越容易完成（降低难度）
- 模糊描述会增加失败率（提高难度）
- 输出格式必须明确，verify.py 依赖它来验证

### 3.2 meta.json — 任务元数据

```json
{
  "task_id": "my_custom_task",
  "task_name": "My Custom Task",
  "category_id": "my_category",
  "category_name": "My Category",
  "description": "一句话描述任务",
  "author": "your_name",
  "created_at": "2025-01-01",
  "difficulty": "L2",
  "tags": ["data extraction"],
  "mcp": ["playwright"],
  "meta_data": {
    "stateType": null,
    "stateContent": null,
    "stateUrl": null,
    "stateOriginalUrl": null
  }
}
```

**⚠️ 关键注意事项**：

| 字段 | 说明 | 踩坑点 |
|------|------|--------|
| `task_id` | 任务唯一标识 | 必须与目录名一致 |
| `category_id` | 分类标识 | **必须全局唯一！不能和官方任务冲突** |
| `mcp` | 使用的 MCP 服务 | 必须与 `--mcp` 参数匹配 |
| `difficulty` | 难度等级 | L1（简单）/ L2（中等）/ L3（困难） |

**category_id 冲突问题**：
- 如果你的 `category_id` 和官方任务相同（如 `"desktop"`），你的 `initial_state` 会覆盖官方任务的测试环境！
- 建议使用独特前缀，如 `"custom_file_mgmt"`, `"custom_log_analysis"`, `"custom_web_extraction"`

### 3.3 verify.py — 验证脚本

验证模型的执行结果，返回 `exit(0)` 表示通过，`exit(1)` 表示失败。

**不同 MCP 服务的验证方式**：

| MCP 服务 | 验证对象 | 读取方式 |
|----------|---------|---------|
| Filesystem | 文件系统中的文件/目录 | 直接读取 `FILESYSTEM_TEST_ROOT/{category_id}/` 下的文件 |
| PostgreSQL | 数据库中的表/视图/函数 | 通过 `psycopg2` 连接数据库查询 |
| GitHub | GitHub 仓库的 issue/PR/label | 通过 GitHub API（使用 `MCP_GITHUB_TOKEN` 环境变量） |
| Playwright | 模型的文本输出（最后一条 assistant 消息） | 读取 `MCP_MESSAGES` 指向的 `messages.json` |

**Filesystem verify.py 模板**：

```python
#!/usr/bin/env python3
import sys, os

def verify():
    base = os.environ.get("FILESYSTEM_TEST_ROOT", "./test_environments")
    category = "your_category_id"
    root = os.path.join(base, category)
    
    # 检查文件是否存在
    if not os.path.exists(os.path.join(root, "expected_file.txt")):
        print("✗ expected_file.txt not found")
        return False
    
    # 检查文件内容
    # ...
    
    return True

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

# ⚠️ 重要：设置 autocommit=True，否则一个 step 的 SQL 错误会导致后续所有 step 级联失败
conn = get_conn()
conn.autocommit = True
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
        # 解析 content 中的 text...
```

---

## 四、initial_state（初始状态）

### 4.1 什么时候需要

| MCP 服务 | 是否需要 initial_state | 说明 |
|----------|----------------------|------|
| Filesystem | ✅ 必须 | 模型操作的初始文件必须预先放好 |
| PostgreSQL | ❌ 不需要 | 使用已有的数据库 |
| GitHub | ✅ 有模板仓库 | 官方用 `initial_state/` 存模板仓库文件 |
| Playwright | ❌ 不需要 | 目标是公开网页，无需本地初始状态 |

### 4.2 Filesystem 初始状态部署

**这是最容易出错的地方！** Filesystem 任务的初始文件必须放到两个位置：

**位置 1**：你的任务目录（存档用）
```
your_data_dir/filesystem/task-1/initial_state/
├── file1.txt
├── file2.log
└── subdir/
    └── file3.dat
```

**位置 2**：MCPMark 的 test_environments（运行时实际读取）
```
MCPMark/mcpmark/test_environments/{category_id}/
├── file1.txt
├── file2.log
└── subdir/
    └── file3.dat
```

**⚠️ 关键**：`test_environments/{category_id}/` 下放的是 `initial_state/` 的**内容**，不是整个 `initial_state` 目录！

```bash
# ✅ 正确
mkdir -p MCPMark/mcpmark/test_environments/my_category
cp -r your_data_dir/filesystem/task-1/initial_state/* \
      MCPMark/mcpmark/test_environments/my_category/

# ❌ 错误（会多一层 initial_state 目录）
cp -r your_data_dir/filesystem/task-1/initial_state \
      MCPMark/mcpmark/test_environments/my_category/
```

### 4.3 category_id 与 test_environments 的对应关系

框架通过 `meta.json` 中的 `category_id` 来查找 `test_environments/{category_id}/`：

```
meta.json: "category_id": "my_category"
     ↓
运行时复制: test_environments/my_category/ → 临时工作目录
     ↓
模型在临时工作目录中操作文件
     ↓
verify.py 检查临时工作目录中的结果
```

**⚠️ 如果两个任务的 category_id 相同，它们会共享 initial_state，互相干扰！**

---

## 五、部署任务到 MCPMark

### 5.1 完整部署步骤（以 Filesystem 任务为例）

```bash
# 1. 设定变量
CATEGORY_ID="my_category"
TASK_ID="my_custom_task"
MCP_SERVICE="filesystem"
MCPMARK_ROOT="MCPMark/mcpmark"
DATA_DIR="your_data_dir/filesystem/task-1"

# 2. 创建任务目录
mkdir -p ${MCPMARK_ROOT}/tasks/${MCP_SERVICE}/standard/${CATEGORY_ID}/${TASK_ID}

# 3. 复制任务文件
cp ${DATA_DIR}/description.md \
   ${DATA_DIR}/meta.json \
   ${DATA_DIR}/verify.py \
   ${MCPMARK_ROOT}/tasks/${MCP_SERVICE}/standard/${CATEGORY_ID}/${TASK_ID}/

# 4. 部署初始状态到 test_environments（仅 Filesystem 需要）
mkdir -p ${MCPMARK_ROOT}/test_environments/${CATEGORY_ID}
cp -r ${DATA_DIR}/initial_state/* \
      ${MCPMARK_ROOT}/test_environments/${CATEGORY_ID}/

# 5. 验证部署
ls ${MCPMARK_ROOT}/tasks/${MCP_SERVICE}/standard/${CATEGORY_ID}/${TASK_ID}/
ls ${MCPMARK_ROOT}/test_environments/${CATEGORY_ID}/
```

### 5.2 Playwright / PostgreSQL / GitHub 部署

Playwright 和 PostgreSQL 不需要 test_environments，只需步骤 2-3。
GitHub 的 initial_state 由框架自动处理（模板仓库导入）。

---

## 六、运行评测

### 6.1 基本命令

```bash
cd MCPMark/mcpmark

pixi run python -m pipeline \
  --exp-name <实验名> \
  --mcp <mcp服务> \
  --tasks <category_id/task_id> \
  --models <模型名> \
  --k <重复轮次>
```

### 6.2 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--exp-name` | 实验名称，决定结果目录名 | `exp-playwright-001` |
| `--mcp` | MCP 服务类型 | `filesystem` / `postgres` / `github` / `playwright` |
| `--tasks` | 任务路径（category_id/task_id） | `my_category/my_custom_task` |
| `--models` | 模型名 | `or-qwen3-coder` |
| `--k` | 独立运行轮次 | `4`（推荐，用于计算 pass@k） |

### 6.3 后台运行（防止 SSH 断开杀进程）

```bash
cd MCPMark/mcpmark && \
nohup pixi run python -m pipeline \
  --exp-name exp-playwright-001 \
  --mcp playwright \
  --tasks my_category/my_custom_task \
  --models or-qwen3-coder \
  --k 4 \
  > log/run.log 2>&1 &
```

> **注意**：`pixi run` 必须在包含 `pyproject.toml`（含 `[tool.pixi]`）的目录下执行，否则会报错 `could not find pixi.toml`。

### 6.4 多任务运行

**不能**用逗号分隔 `--tasks`，必须分开跑：

```bash
# ❌ 错误 — 会报 0/0 tasks
--tasks category_a/task1,category_b/task2

# ✅ 正确 — 每个任务单独跑
pixi run python -m pipeline --tasks category_a/task1 ... && \
pixi run python -m pipeline --tasks category_b/task2 ...
```

### 6.5 结果目录结构

```
results/{exp-name}/{model}__{mcp_service}/run-{n}/
├── summary.json          # 本轮汇总
├── {category_id}__{task_id}/
│   ├── messages.json     # 完整对话记录（SFT 数据来源）
│   ├── trajectory.json   # 操作轨迹
│   └── summary.json      # 任务级汇总
```

---

## 七、查看结果

### 7.1 快速查看通过率

```bash
# 从日志看
grep -E "Tasks passed:|PASSED|FAILED" log/run.log

# 从 summary.json 看
for run in 1 2 3 4; do
  f="results/{exp-name}/{model}__{mcp}/run-${run}/summary.json"
  python3 -c "import json; d=json.load(open('$f')); print(f'run-$run:', 'PASS' if d['success_rate']==100 else 'FAIL')"
done
```

### 7.2 查看详细验证结果

```bash
# 直接看日志中的 Stage 3: Verify 部分
grep -A 20 "Stage 3: Verify" log/run.log
```

---

## 八、常见问题 & 踩坑记录

### 8.1 `Tasks passed: 0/0`

**原因**：`--tasks` 参数路径不对，或 `category_id/task_id` 不匹配。
**排查**：检查 `meta.json` 中的 `category_id` 和 `task_id` 是否与目录结构一致。

### 8.2 Filesystem 任务初始文件找不到

**原因**：`test_environments/{category_id}/` 目录不存在或内容为空。
**排查**：
```bash
ls MCPMark/mcpmark/test_environments/{你的category_id}/
```

### 8.3 PostgreSQL `current transaction is aborted`

**原因**：前一个 SQL 语句报错，整个事务被标记为 aborted，后续所有 SQL 都会失败。
**解决**：在 verify.py 中设置 `conn.autocommit = True`。

### 8.4 GitHub `Cannot import template to a public repository`

**原因**：框架默认创建公开仓库，但 GitHub 不允许往公开仓库导入模板。
**解决**：修改 `github_state_manager.py` 强制使用 `private=True`。

### 8.5 GitHub verify.py 读不到 Token

**原因**：框架传给 verify.py 的环境变量名是 `MCP_GITHUB_TOKEN`，不是 `GITHUB_TOKEN`。
**解决**：verify.py 中优先读取 `MCP_GITHUB_TOKEN`。

### 8.6 Playwright `browser_install` 超时

**原因**：首次运行时 Playwright 需要下载浏览器。
**解决**：提前运行 `npx -y playwright install chromium && npx -y playwright install-deps chromium`。

### 8.7 Markdown 中 `x/y` 渲染成日期

**原因**：某些 Markdown 渲染器把 `3/4` 当成日期。
**解决**：用反引号包裹：`` `3/4` ``。

### 8.8 进程被 SSH 断开杀死

**解决**：使用 `nohup ... &` 后台运行，日志输出到文件。

### 8.9 `could not find pixi.toml` 错误

**原因**：`pixi run` 不在 MCPMark/mcpmark 目录下执行。
**解决**：先 `cd MCPMark/mcpmark` 再执行 `pixi run`。多条 `nohup` 命令时，每条前都要加 `cd`。

---

## 九、难度调控方法论

### 9.1 影响难度的因素

| 因素 | 降低难度 | 提高难度 |
|------|---------|---------|
| 步骤数量 | 减少步骤 | 增加步骤 |
| 指令清晰度 | 详细具体的步骤说明 | 模糊/高层次描述 |
| 验证严格度 | 宽松匹配（contains） | 严格匹配（exact） |
| 边界条件 | 简单直接的数据 | 含陷阱的边界数据 |
| 多步依赖 | 步骤独立 | 步骤间有依赖链 |
| 输出格式 | 自由格式 | 严格模板（如 `<answer>` 标签） |

### 9.2 目标通过率

| 用途 | 目标通过率 | 说明 |
|------|-----------|------|
| SFT 正样本为主 | 75% (3/4) | 多数成功，少数失败 |
| RL 混合样本 | 50% (2/4) | 成功失败各半 |
| RL 负样本为主 | 25% (1/4) | 多数失败，少数成功 |
| 难度天花板 | 0% (0/4) | 纯负样本 |

### 9.3 迭代流程

```
设计任务 → 跑目标模型 k=4 → 分析通过率
                                ↓
                     通过率过高 → 增加步骤 / 严格验证 / 增加陷阱
                     通过率过低 → 简化步骤 / 放宽验证 / 添加提示
                     通过率合适 → 跑 SOTA 对比 → 打包交付
```

---

## 十、数据产出 & 交付

### 10.1 产出物

每个任务跑完后产出：

| 文件 | 用途 |
|------|------|
| `messages.json` | 完整对话记录 → **SFT 训练数据** |
| `trajectory.json` | 操作轨迹 → **SFT 训练数据** |
| `verify.py` 结果 | 通过/失败 → **RL reward 信号** |

### 10.2 打包交付

```bash
cd your_data_dir/playwright
zip -r pw-task-1.zip pw-task-1/
```

### 10.3 汇总报告

建议维护一份 sample_data.md 汇总文档，记录每个任务的：
- 任务描述
- 目标模型通过率 & 各 run 详情
- SOTA 对比数据
- 失败模式分析
- Sample Data 价值评估
