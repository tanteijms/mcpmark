Please use PostgreSQL tools to finish the following task:

### Task Description

You are a data analyst building an analytics layer on top of the Chinook music store database. The database already contains tables for customers, invoices, invoice lines, tracks, albums, artists, and genres. Your task is to create analytics infrastructure: summary tables, views, functions, triggers, and indexes that enable business intelligence queries.

### Database Schema (Key Tables)

- `"Customer"` — CustomerId, FirstName, LastName, Company, City, State, Country, Email, SupportRepId
- `"Invoice"` — InvoiceId, CustomerId, InvoiceDate, BillingCountry, Total
- `"InvoiceLine"` — InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity
- `"Track"` — TrackId, Name, AlbumId, GenreId, Composer, Milliseconds, Bytes, UnitPrice
- `"Genre"` — GenreId, Name
- `"Album"` — AlbumId, Title, ArtistId
- `"Artist"` — ArtistId, Name

### Task Objectives

#### 1. Create Materialized View: `monthly_revenue`

Create a materialized view that aggregates invoice data by year, month, and billing country:

```sql
-- Expected columns:
-- sale_year (INT), sale_month (INT), country (VARCHAR),
-- total_revenue (NUMERIC), invoice_count (INT), avg_invoice (NUMERIC rounded to 2 decimals)
```

- Extract year and month from `"InvoiceDate"`
- Group by year, month, and `"BillingCountry"`
- `total_revenue` = SUM of `"Total"`
- `invoice_count` = COUNT of invoices
- `avg_invoice` = ROUND(AVG of `"Total"`, 2)

#### 2. Create Table: `customer_analytics`

Create and populate a table with per-customer analytics:

```sql
-- Expected columns:
-- customer_id (INT PRIMARY KEY), full_name (VARCHAR), email (VARCHAR),
-- country (VARCHAR), total_spent (NUMERIC), num_purchases (INT),
-- avg_purchase (NUMERIC rounded to 2 decimals),
-- first_purchase (DATE), last_purchase (DATE), customer_segment (VARCHAR)
```

**Customer segments** based on `total_spent`:
- `'VIP'` — total_spent > 45.00
- `'Regular'` — total_spent >= 25.00 AND total_spent <= 45.00
- `'Occasional'` — total_spent < 25.00

Populate this table for ALL customers who have at least 1 invoice.

#### 3. Create Table: `genre_country_rankings`

Create and populate a table showing the top 3 genres by revenue for each billing country:

```sql
-- Expected columns:
-- country (VARCHAR), genre_name (VARCHAR), genre_revenue (NUMERIC rounded to 2 decimals),
-- country_rank (INT)
```

- Revenue = SUM(`"InvoiceLine"."UnitPrice"` * `"InvoiceLine"."Quantity"`) per genre per country
- Use a window function: `RANK() OVER (PARTITION BY country ORDER BY genre_revenue DESC)`
- **Only include rows where country_rank <= 3**
- Join path: `"Invoice"` → `"InvoiceLine"` → `"Track"` → `"Genre"`, country from `"Invoice"."BillingCountry"`

#### 4. Create Function: `get_customer_top_genre`

Create a SQL/PL-pgSQL function:

```sql
CREATE FUNCTION get_customer_top_genre(p_customer_id INT)
RETURNS VARCHAR
```

- Returns the genre name where the customer has spent the most money
- Spending = SUM(`"InvoiceLine"."UnitPrice"` * `"InvoiceLine"."Quantity"`)
- Join: `"Invoice"` → `"InvoiceLine"` → `"Track"` → `"Genre"`, filtered by `"Invoice"."CustomerId"`
- If the customer has no purchases, return `'No purchases'`
- If there's a tie, return any one of the tied genres

#### 5. Create Audit Trigger

Create an audit log system for the `"Customer"` table:

```sql
-- Table: customer_audit_log
-- Columns: log_id (SERIAL PRIMARY KEY), action (VARCHAR),
--          customer_id (INT), changed_at (TIMESTAMP DEFAULT NOW()),
--          old_data (JSONB), new_data (JSONB)
```

Create a trigger function `fn_customer_audit()` that:
- On INSERT: logs action='INSERT', new_data=row_to_json(NEW), old_data=NULL
- On UPDATE: logs action='UPDATE', old_data=row_to_json(OLD), new_data=row_to_json(NEW)
- On DELETE: logs action='DELETE', old_data=row_to_json(OLD), new_data=NULL

Attach the trigger to `"Customer"` table for INSERT, UPDATE, DELETE operations.

#### 6. Create Performance Indexes

Create the following indexes:
- `idx_invoice_customer` on `"Invoice"("CustomerId")`
- `idx_invoiceline_track` on `"InvoiceLine"("TrackId")`
- `idx_customer_analytics_segment` on `customer_analytics(customer_segment)`
- `idx_genre_country_rank` on `genre_country_rankings(country, country_rank)`

### Constraints

- Use exact table and column names as specified
- All monetary values must be NUMERIC type, rounded to 2 decimal places where specified
- The materialized view must be refreshable (`CREATE MATERIALIZED VIEW`)
- The function must handle edge cases (no purchases → return 'No purchases')
- The trigger must handle all three DML operations (INSERT, UPDATE, DELETE)
- All existing data must remain unchanged

### Expected Outcome

After task completion:
- `monthly_revenue` materialized view exists and returns correct aggregations
- `customer_analytics` table is populated with correct segments for all purchasing customers
- `genre_country_rankings` table contains only top-3 genres per country
- `get_customer_top_genre()` function returns correct genre for any customer
- `customer_audit_log` table and trigger exist and fire correctly
- All 4 indexes are created
- All numbers match the underlying data exactly

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
