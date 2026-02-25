请使用 FileSystem 工具完成以下任务：

### 任务描述

你是一名数据工程师，负责清理一个大型团队共享工作区。多名团队成员在过去几个月中将文件随意存放在多层嵌套子目录中。工作区包含 CSV、JSON、TXT 文件，分散在 `inbox/`、`downloads/`（含按季度日期命名的子目录）、`shared/`、`archive/` 以及根目录中。这些文件存在多种问题：

- **命名不统一**：大小写混用、文件名含空格、扩展名大写
- **重复文件**：某些文件以不同文件名存在于多个位置，但**内容逐字节完全相同**
- **近似重复**：某些文件名称/内容非常相似但**略有不同**（如新增了数据的更新版本）——这些不是重复项，必须同时保留
- **数据损坏**：部分 JSON 文件包含语法错误（缺少括号、尾逗号、使用单引号等），无法正常解析
- **空文件**：部分文件内容为空或仅包含空白字符
- **草稿文件**：部分文件是初步草稿（文件名中包含"DRAFT"，不区分大小写）
- **隐藏文件**：以 `.` 开头的文件（如 `.gitignore`）应保留不动
- **优先级冲突**：某些文件可能匹配多条规则（如一个既是草稿又是空的文件）——必须按严格优先级顺序应用规则

你的任务是系统性地清洗、验证、去重并组织整个工作区。

### 具体要求

1. **递归扫描所有子目录**，找到工作区中的每一个文件

2. **创建目标目录结构**：
   - `organized/csv/`、`organized/json/`、`organized/txt/` — 存放有效的唯一数据文件
   - `drafts/` — 存放草稿文件
   - `quarantine/` — 存放损坏/格式错误的文件
   - `trash/` — 存放空文件或仅含空白的文件

3. **按严格优先级顺序对每个 `.csv`、`.json`、`.txt` 文件执行处理规则**：

   **规则 A — 空文件检查（最高优先级）**：如果文件为空或仅包含空白字符，移至 `trash/`。此规则优先于所有其他规则——即使文件名包含"DRAFT"，空文件也应进入 trash 而非 drafts。

   **规则 B — 草稿识别**：如果文件名包含"DRAFT"（不区分大小写）且文件非空，移至 `drafts/`。文件名规范化（全小写、空格替换为下划线）。

   **规则 C — JSON 验证**：对于 `.json` 文件，验证内容是否为有效 JSON（检查缺少的闭合括号、尾逗号、单引号代替双引号等语法错误）。如果无法解析为有效 JSON，移至 `quarantine/` 并追加 `.invalid` 扩展名。

   **规则 D — 重复检测**：比较文件内容以检测**完全重复**（逐字节相同）。如果两个或多个文件内容完全相同，仅保留一份（按完整原始路径字母顺序排列的第一个），其余不归档。**重要**：内容相似但不完全相同的文件（如新增了数据行的更新版本）不是重复项，必须同时保留。

   **规则 E — 归档整理**：将剩余的有效、唯一文件移入 `organized/{类型}/`。文件名规范化：全小写、空格替换为下划线。

4. **保留非目标文件**：非目标扩展名的文件（`.md`、`.gitignore` 等）和隐藏文件（以 `.` 开头）必须保持原位不变。

5. **生成三份报告文件**（位于工作区根目录）：

   **`inventory.md`** — 按类型列出所有已归档文件，含文件大小：
   ```
   # File Inventory

   ## csv (N files)
   - filename.csv (X.X KB)
   ...
   Subtotal: X.X KB

   ## json (N files)
   - filename.json (X.X KB)
   ...
   Subtotal: X.X KB

   ## txt (N files)
   - filename.txt (X.X KB)
   ...
   Subtotal: X.X KB

   Total: N files organized, X.X KB total
   ```
   文件大小 = `字节数 / 1024`，保留 1 位小数。分类内按字母排序。含各类小计和总计。

   **`duplicates_report.md`** — 记录所有检测到的重复文件组：
   ```
   # Duplicates Report

   ## Duplicate Group 1
   - Kept: <保留的文件路径>
   - Removed: <重复文件路径>
   ...

   Total: N duplicate files removed
   ```

   **`audit_summary.md`** — 提供处理统计：
   ```
   # Audit Summary

   - Total files scanned: N
   - Files organized: N (csv: N, json: N, txt: N)
   - Duplicates removed: N
   - Files quarantined: N
   - Draft files separated: N
   - Empty files discarded: N
   - Files preserved (non-target): N
   ```
   所有数字必须内部一致，且与目录实际状态匹配。

### 约束条件

- 不得修改任何数据文件的内容——只做移动、重命名和整理
- 只处理 `.csv`、`.json`、`.txt` 扩展名的文件（大小写不敏感）
- 所有非目标文件（`.md`、`.gitignore` 等）和隐藏文件必须保持原位不变
- 规则优先级不可违反：A > B > C > D > E
- 报告必须内部一致——audit_summary.md 中的数字必须与目录实际内容和 inventory.md 匹配
- 去重基于实际文件内容而非文件名——名称相似但内容不同的文件不是重复项

### 预期结果

任务完成后，工作区应当呈现以下状态：
- `organized/csv/` 包含唯一有效的 CSV 文件（已正确重命名）
- `organized/json/` 包含有效可解析的 JSON 文件（已正确重命名）
- `organized/txt/` 包含非草稿、非空的 TXT 文件（已正确重命名）
- `drafts/` 包含非空的草稿文件
- `quarantine/` 包含已标记的损坏 JSON 文件
- `trash/` 包含空文件（包括空的草稿）
- 三份报告文件包含准确且内部一致的统计数据
- 所有 `.md` 文件和隐藏文件保持原位不变

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
