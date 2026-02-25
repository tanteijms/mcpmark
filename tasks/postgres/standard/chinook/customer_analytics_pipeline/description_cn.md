请使用 PostgreSQL 工具完成以下任务：

### 任务描述

你是一名数据分析师，需要在 Chinook 音乐商店数据库上构建分析层。数据库中已有客户、发票、发票明细、曲目、专辑、艺术家和流派等表。你的任务是创建分析基础设施：汇总表、视图、函数、触发器和索引，以支持商业智能查询。

### 数据库表结构（核心表）

- `"Customer"` — CustomerId, FirstName, LastName, Company, City, State, Country, Email, SupportRepId
- `"Invoice"` — InvoiceId, CustomerId, InvoiceDate, BillingCountry, Total
- `"InvoiceLine"` — InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity
- `"Track"` — TrackId, Name, AlbumId, GenreId, Composer, Milliseconds, Bytes, UnitPrice
- `"Genre"` — GenreId, Name
- `"Album"` — AlbumId, Title, ArtistId
- `"Artist"` — ArtistId, Name

### 任务目标

#### 1. 创建物化视图：`monthly_revenue`

创建按年、月、国家汇总发票数据的物化视图：

- 列：`sale_year` (INT), `sale_month` (INT), `country` (VARCHAR), `total_revenue` (NUMERIC), `invoice_count` (INT), `avg_invoice` (NUMERIC 保留2位小数)
- 从 `"InvoiceDate"` 提取年和月
- 按年、月、`"BillingCountry"` 分组
- `total_revenue` = SUM(`"Total"`)
- `invoice_count` = COUNT
- `avg_invoice` = ROUND(AVG(`"Total"`), 2)

#### 2. 创建并填充表：`customer_analytics`

- 列：`customer_id` (INT PRIMARY KEY), `full_name` (VARCHAR), `email` (VARCHAR), `country` (VARCHAR), `total_spent` (NUMERIC), `num_purchases` (INT), `avg_purchase` (NUMERIC 保留2位小数), `first_purchase` (DATE), `last_purchase` (DATE), `customer_segment` (VARCHAR)

**客户分层**规则（基于 `total_spent`）：
- `'VIP'` — total_spent > 45.00
- `'Regular'` — total_spent >= 25.00 AND total_spent <= 45.00
- `'Occasional'` — total_spent < 25.00

为所有至少有 1 张发票的客户填充数据。

#### 3. 创建并填充表：`genre_country_rankings`

展示每个国家收入最高的前 3 个流派：

- 列：`country` (VARCHAR), `genre_name` (VARCHAR), `genre_revenue` (NUMERIC 保留2位小数), `country_rank` (INT)
- 收入 = SUM(`"InvoiceLine"."UnitPrice"` * `"InvoiceLine"."Quantity"`)
- 使用窗口函数：`RANK() OVER (PARTITION BY country ORDER BY genre_revenue DESC)`
- **仅保留 country_rank <= 3 的行**
- 连接路径：`"Invoice"` → `"InvoiceLine"` → `"Track"` → `"Genre"`，国家来自 `"Invoice"."BillingCountry"`

#### 4. 创建函数：`get_customer_top_genre`

```sql
CREATE FUNCTION get_customer_top_genre(p_customer_id INT) RETURNS VARCHAR
```

- 返回客户消费最多的流派名称
- 消费 = SUM(`"InvoiceLine"."UnitPrice"` * `"InvoiceLine"."Quantity"`)
- 无购买记录则返回 `'No purchases'`
- 如有并列，返回任意一个

#### 5. 创建审计触发器

为 `"Customer"` 表创建审计日志系统：

- 审计表 `customer_audit_log`：`log_id` (SERIAL), `action` (VARCHAR), `customer_id` (INT), `changed_at` (TIMESTAMP), `old_data` (JSONB), `new_data` (JSONB)
- 触发器函数 `fn_customer_audit()`：
  - INSERT → action='INSERT', new_data=行数据, old_data=NULL
  - UPDATE → action='UPDATE', old_data=旧数据, new_data=新数据
  - DELETE → action='DELETE', old_data=旧数据, new_data=NULL
- 绑定到 `"Customer"` 表的 INSERT/UPDATE/DELETE 操作

#### 6. 创建性能索引

- `idx_invoice_customer` on `"Invoice"("CustomerId")`
- `idx_invoiceline_track` on `"InvoiceLine"("TrackId")`
- `idx_customer_analytics_segment` on `customer_analytics(customer_segment)`
- `idx_genre_country_rank` on `genre_country_rankings(country, country_rank)`

### 约束条件

- 使用精确的表名和列名
- 所有金额使用 NUMERIC 类型，指定位置保留 2 位小数
- 物化视图必须可刷新（`CREATE MATERIALIZED VIEW`）
- 函数须处理边界情况（无购买 → 返回 'No purchases'）
- 触发器须处理三种 DML 操作
- 不修改现有数据

### 预期结果

- `monthly_revenue` 物化视图存在且数据正确
- `customer_analytics` 表已填充，分层正确
- `genre_country_rankings` 仅含每国前 3 流派
- `get_customer_top_genre()` 函数对任意客户返回正确结果
- `customer_audit_log` 表和触发器存在且正常工作
- 4 个索引已创建
- 所有数值与底层数据精确匹配

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
