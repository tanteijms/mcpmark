# Sample Data 可用任务汇总 (2026-02-13)

> 本文档汇总当前已测试并可用于 Qwen3 Coder sample data 的 5 个任务。

## 一、任务总览

注：对比sota为：Claude Opus 4.6   GPT 5.2   Gemini 3 pro   GLM 5

| **#** | **Task ID** | **类型**   | **任务名称**                 | **MCP** **服务** | **Qwen3 通过率** | **SOTA** **通过率**                        |
| ----- | ----------- | ---------- | ---------------------------- | ---------------- | ---------------- | ------------------------------------------ |
| 1     | file-1-v1   | Filesystem | 文件清理与归档               | filesystem       | 3/4 (75%)        | Claude 4/4, GPT 4/4, Gemini 4/4, GLM-5 3/4 |
| 2     | file-1-v2   | Filesystem | 文件清理、去重与归档（进阶） | filesystem       | 1/4 (25%)        | Claude 4/4, GPT 4/4, Gemini 2/4, GLM-5 4/4 |
| 3     | file-1-v3   | Filesystem | 文件清理、去重与归档（高阶） | filesystem       | 0/4 (0%)         | Claude 4/4, GPT 4/4, Gemini 3/4, GLM-5 2/4 |
| 4     | file-3      | Filesystem | 配置迁移与审计               | filesystem       | 1/4 (25%)        | Claude 4/4, GPT 4/4, Gemini 4/4, GLM-5 3/4 |
| 5     | postgre-1   | PostgreSQL | 客户分析数据管道             | postgres         | 3/4 (75%)        | Claude 4/4, GPT 0/4, Gemini 0/4, GLM-5 4/4 |
| 6     | github-1-v3 | GitHub     | 仓库健康审计与修复（简化版） | github           | 2/4 (50%)        | Claude 1/4, GPT 1/4, Gemini 1/4, GLM-5 1/4 |
| 7     | pw-1        | Playwright | PyPI 包信息提取              | playwright       | 1/4 (25%)        | Claude 4/4, GPT 4/4, Gemini 4/4, GLM-5 4/4 |

## 二、各任务详情

### Task 1: file-1-v1 — 文件清理与归档

https://meetchances.feishu.cn/record/Ql8cr5lH3ejOm3cIdQ5cNiPbnPc

**任务描述**：在指定目录中按规则清理临时文件、按类型归档文件到子目录，创建文件清单摘要。

**难度**：低（入门级）

**Qwen3** **Coder** **表现**：

| **Run** | **成功** | **耗时** | **Turns** |
| ------- | -------- | -------- | --------- |
| run-1   | **成功** | 61.4s    | 46        |
| run-2   | **成功** | 44.7s    | 36        |
| run-3   | **成功** | 41.4s    | 44        |
| run-4   | 失败     | 48.3s    | 41        |

**SOTA 对比**：Claude 4/4、GPT 4/4、Gemini 4/4，均全通过。v1 难度偏低，SOTA 无区分度。

**Sample Data 价值**：可作为 SFT 正样本（3 轮成功 trajectory）+ RL 混合样本。

### Task 2: file-1-v2 — 文件清理、去重与归档（进阶）

https://meetchances.feishu.cn/record/LmVorop16eBH8QczvDLccWjRn2g

**任务描述**：在 v1 基础上增加 MD5 去重、文件大小过滤、嵌套目录处理、归档时保留目录结构等要求。

**难度**：中（新增去重逻辑和边界条件）

**Qwen3** **Coder** **表现**：

| **Run** | **成功** | **耗时** | **Turns** |
| ------- | -------- | -------- | --------- |
| run-1   | **成功** | 111.5s   | 51        |
| run-2   | 失败     | 84.8s    | 48        |
| run-3   | 失败     | 128.2s   | 58        |
| run-4   | 失败     | 130.9s   | 84        |

**SOTA** **对比**：Claude 4/4、GPT 4/4、Gemini 2/4。Gemini 开始出现失败，有区分度。

**Sample Data 价值**：1 轮成功 + 3 轮失败，适合 RL reward 信号训练。

### Task 3: file-1-v3 — 文件清理、去重与归档（高阶）

https://meetchances.feishu.cn/record/PkPxro0wzeIDEBc1uQ7cEYHCnic

**任务描述**：在 v2 基础上进一步增加 tar.gz 压缩归档、基于文件内容的智能分类、审计日志生成、符号链接处理等高级要求。

**难度**：高（多步骤复合操作 + 边界条件陷阱）

**Qwen3** **Coder** **表现**：

| **Run** | **成功** | **耗时** | **Turns** |
| ------- | -------- | -------- | --------- |
| run-1   | 失败     | 145.6s   | 51        |
| run-2   | 失败     | 123.5s   | 88        |
| run-3   | 失败     | 87.0s    | 56        |
| run-4   | 失败     | 92.4s    | 51        |

**SOTA** **对比**：Claude 4/4、GPT 4/4、Gemini 3/4。SOTA 模型依然能通过，但 Qwen 0/4 全挂。

**Sample Data 价值**：纯失败样本，适合分析 Qwen 的能力天花板，可用于 RL 负样本。

### Task 4: file-3 — 配置迁移与审计

https://meetchances.feishu.cn/record/CI9qrY7dXewzyXcBBTfcWoLXnxb

**任务描述**：将多种格式（INI/YAML/JSON）的旧配置文件统一迁移为标准化 YAML 格式，生成迁移审计报告，处理格式转换冲突和数据类型保持。

**难度**：中高（跨格式转换 + 审计逻辑）

**Qwen3** **Coder** **表现**：

| **Run** | **成功** | **耗时** | **Turns** |
| ------- | -------- | -------- | --------- |
| run-1   | 失败     | 172.3s   | 77        |
| run-2   | 失败     | 426.6s   | 100       |
| run-3   | 失败     | 131.2s   | 75        |
| run-4   | **成功** | 99.1s    | 48        |

**SOTA** **对比**：Claude 4/4、GPT 4/4、Gemini 4/4，均全通过。

**Sample Data 价值**：1 轮成功 + 3 轮失败，run-2 耗时 427s 达到 100 turns 仍失败，可分析模型在长会话中的退化行为。

### Task 5: postgre-1 — 客户分析数据管道

https://meetchances.feishu.cn/record/IcwVruSO7evh8VcGfEqcEPRAn2b

**任务描述**：基于 Chinook 数据库，完成 12 步 PostgreSQL 数据管道建设：创建物化视图（monthly_revenue）、客户分析表（customer_analytics + 分段逻辑）、流派国家排名表（genre_country_rankings + Top3 筛选）、存储函数（get_customer_top_genre）、审计触发器（Customer 表 INSERT/UPDATE/DELETE）、性能索引。

**难度**：高（12 个验证步骤，涵盖 DDL/DML/函数/触发器/索引）

**Qwen3** **Coder** **表现**（verify.py 修复后重跑）：

| **Run** | **成功** | **得分**  | **耗时** | **Turns** |
| ------- | -------- | --------- | -------- | --------- |
| run-1   | 失败     | 8/12      | 65.2s    | 38        |
| run-2   | **成功** | **12/12** | 80.8s    | 24        |
| run-3   | **成功** | **12/12** | 81.0s    | 25        |
| run-4   | **成功** | **12/12** | 60.9s    | 26        |

**SOTA 对比**：Claude 4/4, GPT 0/4, Gemini 0/4, GLM-5 4/4

**Sample Data 价值**：3 轮满分 + 1 轮 8/12，表现优秀。满分 trajectory 可直接作为 SFT 数据。

### Task 6: github-1-v3 — 仓库健康审计与修复（简化版）

https://meetchances.feishu.cn/record/WNPorXegpeOjV2cvEAecJLsVnxe

**任务描述**：接管一个 GitHub 仓库，执行结构化健康审计：创建 8 个标准化标签（audit:critical/high/medium/low + type:bug/docs/security/maintenance），创建 5 个审计 issue 并打上正确标签，创建修复分支提交 CONTRIBUTING.md/LICENSE/SECURITY.md 三个文件，创建 PR，创建汇总 issue 交叉引用所有发现，并为每个审计 issue 添加修复计划评论。

**难度**：中低（L1，从 v1 的 L3 逐步简化而来）

**迭代历程**：v1（12 step, 含 milestone + PR 引用）→ v2（10 step, 去 milestone）→ v3（9 step, 去 PR issue 引用）

**Qwen3 Coder 表现**：

| **Run** | **成功** | **得分** | **耗时** | **Turns** |
| ------- | -------- | -------- | -------- | --------- |
| run-1   | **成功** | **9/9**  | 110.4s   | 38        |
| run-2   | 失败     | 8/9      | 95.3s    | 37        |
| run-3   | **成功** | **9/9**  | 124.9s   | 43        |
| run-4   | 失败     | 8/9      | 45.2s    | 17        |

**失败模式**：唯一失败点是 Step 1（8 个标签创建不全），2/4 轮次未创建全部 8 个自定义标签。其余 8 个 step 全部 4/4 通过。

**Sample Data 价值**：2 轮满分成功 trajectory 可作为 SFT 正样本，2 轮 8/9 失败样本可用于 RL reward 训练。标签创建是唯一波动点，适合针对性训练模型对"精确枚举操作"的稳定性。

### **Task 7: pw-1-v2 — PyPI 依赖链调查（多页导航）**

https://meetchances.feishu.cn/record/CFP4rHkUAeMUtMcAjfDcmlKGn6c

**任务描述**：使用 Playwright MCP 工具依次访问 3 个 PyPI 页面（Flask 3.0.0 → Werkzeug 3.0.0 → Jinja2 3.1.2），从每个页面提取结构化元数据（依赖列表、Python 版本、摘要），并跨页推理出共享传递依赖（MarkupSafe），以 `<answer>` 标签格式输出 10 个字段。

**难度**：L3（多页导航 + 跨页信息综合 + 依赖区分）

**挑战点**：

- 连续访问 3 个不同 PyPI 页面（6-8 次 Playwright 工具调用）
- 区分 required 依赖 vs optional/extras 依赖
- 正确处理条件依赖（importlib-metadata 有 Python 版本条件）
- 跨页推理：识别 Werkzeug 和 Jinja2 的共享传递依赖

**Qwen3** **Coder** **表现**：

| Run   | 成功 | 得分 | 说明                                           |
| ----- | ---- | ---- | ---------------------------------------------- |
| run-1 | 失败 | 8/10 | FlaskDepCount=3（应为6），FlaskDeps 只找到 3/6 |
| run-2 | 失败 | 0/10 | Agent 执行崩溃（工具调用序列化失败）·          |
| run-3 | 失败 | 9/10 | FlaskDepCount=4（应为6），其余 9 个字段全对    |
| run-4 | 失败 | 8/10 | FlaskDepCount=3（应为6），FlaskDeps 只找到 4/6 |

**失败模式**：多页导航和跨页推理完全正确（Werkzeug/Jinja2/SharedDep 3 次有效运行全对），唯一短板是 **Flask** **依赖列表提取不完整**——模型反复漏掉部分依赖（importlib-metadata、blinker 等）。Run 3 差一点就过了（9/10）。

**SOTA** **对比**：Claude 4/4, GPT 4/4, Gemini 4/4, GLM-5 3/4。SOTA 全部高通过率，任务设计合理。

**与 pw-1 对比**：pw-1 的失败是工具调用 JSON 序列化 bug（非智力因素），pw-1-v2 的失败是信息提取遗漏（智力因素），**训练信号质量显著提升**。

**Sample Data 价值**：4 轮失败但错误模式清晰（信息提取能力不足），适合 RL 负样本训练。跨页推理能力已具备，仅需提升页面信息提取完整性。