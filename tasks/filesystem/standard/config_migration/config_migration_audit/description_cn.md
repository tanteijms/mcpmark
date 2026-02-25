请使用 FileSystem 工具完成以下任务：

### 任务描述

你是一名 DevOps 工程师，负责将一个遗留项目的配置从 INI 格式迁移到 YAML 格式。项目在 `configs/` 目录下有 8 个 INI 配置文件，分别管理系统的不同方面（数据库、服务器、缓存、认证、日志、监控、通知、遗留 API）。迁移必须遵循 `migration_spec.md` 中定义的规则。

主要挑战：
- 部分 INI section 标记为**已弃用**（带 `; DEPRECATED` 注释），不能迁移到 YAML — 需单独记录
- 有一整个文件（`legacy_api.ini`）完全弃用
- 值必须在 YAML 中保持**正确的类型**（整数、布尔值、浮点数不加引号；含特殊字符的字符串需加引号）
- **逗号分隔的值**应转换为 YAML 列表
- 存在**跨文件冲突**：不同文件中出现同名 key 但值不同 — 必须检测并报告
- 所有原始文件必须在处理前**备份**

### 具体要求

1. **阅读迁移规范** `migration_spec.md`，了解所有规则

2. **创建输出目录**：`yaml/`、`backup/`

3. **备份原始文件**：将每个 `.ini` 文件复制到 `backup/`，添加时间戳后缀（如 `database.ini` → `backup/database_20260211.ini`）

4. **将每个 INI 文件转换为 YAML 格式**：
   - 每个 `[section]` 变为 YAML 顶层键
   - 键值对嵌套在其 section 下
   - **类型保留**：
     - 整数（如 `port = 5432`）→ `port: 5432`（不加引号）
     - 布尔值（如 `enabled = true`）→ `enabled: true`（不加引号）
     - 浮点数（如 `error_rate_warning = 0.01`）→ `error_rate_warning: 0.01`
     - 逗号分隔列表（如 `hosts = a,b,c`）→ YAML 列表格式
     - 含特殊字符的字符串 → 加引号
   - **跳过弃用 section** — 不包含在 YAML 输出中
   - 对完全弃用的 `legacy_api.ini`，创建一个仅含弃用注释的 YAML 文件

5. **生成 `deprecated.log`** 列出所有弃用 section：
   ```
   [database.ini] replication: Old replication settings, use new cluster config instead
   [server.ini] static: Old static file serving, moved to CDN
   ...
   ```

6. **检测跨文件 key 冲突**，生成 `conflicts.md`：
   - 扫描所有文件的非弃用 section
   - 找出同名 key 在不同文件中有不同值的情况
   - 报告格式：
   ```
   # Cross-File Key Conflicts

   ## Key: connection_timeout
   | File | Section | Value |
   |------|---------|-------|
   | database.ini | connection | 30 |
   | cache.ini | redis | 10 |
   ```

7. **生成 `changelog.md`** 汇总迁移情况：
   ```
   # Configuration Migration Changelog

   ## database.ini → yaml/database.yaml
   - Sections migrated: N
   - Sections deprecated: N
   - Keys migrated: N
   ...
   ```

### 约束条件

- 不得修改原始 INI 文件 — 仅读取
- YAML 文件必须语法正确
- 弃用 section 不得出现在任何 YAML 输出文件中
- 以 `;` 开头的 INI 注释应转为 YAML 的 `#` 注释（仅保留文件头注释）
- 类型检测必须准确 — 端口号 `"5432"` 作为字符串在 YAML 中是不正确的
- 备份文件名必须包含日期后缀

### 预期结果

任务完成后：
- `yaml/` 目录有 8 个 YAML 文件（7 个有内容，1 个几乎为空用于 legacy_api）
- `backup/` 目录有 8 个带时间戳后缀的 INI 备份文件
- `deprecated.log` 列出来自 6 个文件的全部 8 个弃用 section
- `conflicts.md` 记录跨文件 key 名称冲突
- `changelog.md` 包含逐文件的迁移汇总
- 任何 YAML 文件中不包含弃用 section 的内容
- YAML 格式正确，类型保留准确

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
