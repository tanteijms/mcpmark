#!/usr/bin/env python3
"""
Verification for Customer Analytics & Genre Rankings (PostgreSQL MCP)
12 checks covering materialized view, tables, function, trigger, indexes.

Uses the Chinook database (59 customers, 412 invoices, 2240 invoice lines).
Ground truth is computed from the live database to avoid hardcoding.
"""

import sys
import os
import psycopg2
import psycopg2.extras


def get_conn():
    """Get a database connection."""
    params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "database": os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USERNAME"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }
    if not params["database"]:
        raise ValueError("POSTGRES_DATABASE env var required")
    return psycopg2.connect(**params)


def run_query(conn, sql, params=None):
    """Run a query and return results."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def run_scalar(conn, sql, params=None):
    """Run a query and return a single scalar value."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


def check_relation_exists(conn, name, relkind='r'):
    """Check if a relation (table/view/matview) exists."""
    kind_map = {'r': 'table', 'v': 'view', 'm': 'materialized view'}
    sql = """
        SELECT 1 FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = %s AND c.relkind = %s AND n.nspname = 'public'
    """
    result = run_scalar(conn, sql, (name, relkind))
    return result is not None


# ============================================================
# Step 1: monthly_revenue materialized view exists
# ============================================================
def verify_matview_exists(conn) -> bool:
    if check_relation_exists(conn, 'monthly_revenue', 'm'):
        print("  [PASS] Materialized view 'monthly_revenue' exists")
        return True
    # Also accept as regular view
    if check_relation_exists(conn, 'monthly_revenue', 'v'):
        print("  [WARN] 'monthly_revenue' is a regular view (expected materialized)")
        return True
    print("  [FAIL] 'monthly_revenue' not found as materialized view or view")
    return False


# ============================================================
# Step 2: monthly_revenue data correctness
# ============================================================
def verify_matview_data(conn) -> bool:
    all_ok = True

    # Check columns exist
    try:
        rows = run_query(conn, "SELECT * FROM monthly_revenue LIMIT 1")
        if rows:
            cols = set(rows[0].keys())
            required_cols = {'sale_year', 'sale_month', 'country', 'total_revenue', 'invoice_count', 'avg_invoice'}
            missing = required_cols - cols
            if missing:
                print(f"  [FAIL] Missing columns: {missing}")
                return False
            print("  [PASS] All required columns present")
        else:
            print("  [FAIL] monthly_revenue is empty")
            return False
    except Exception as e:
        print(f"  [FAIL] Cannot query monthly_revenue: {e}")
        return False

    # Spot-check: total revenue should match Invoice table
    expected_total = run_scalar(conn, 'SELECT ROUND(SUM("Total")::numeric, 2) FROM "Invoice"')
    actual_total = run_scalar(conn, "SELECT ROUND(SUM(total_revenue)::numeric, 2) FROM monthly_revenue")

    if expected_total and actual_total and abs(float(expected_total) - float(actual_total)) < 0.02:
        print(f"  [PASS] Total revenue matches: {actual_total} (expected {expected_total})")
    else:
        print(f"  [FAIL] Revenue mismatch: got {actual_total}, expected {expected_total}")
        all_ok = False

    # Check row count > 0
    count = run_scalar(conn, "SELECT COUNT(*) FROM monthly_revenue")
    if count and count > 0:
        print(f"  [PASS] monthly_revenue has {count} rows")
    else:
        print("  [FAIL] monthly_revenue has no rows")
        all_ok = False

    return all_ok


# ============================================================
# Step 3: customer_analytics table exists and has correct columns
# ============================================================
def verify_customer_analytics_exists(conn) -> bool:
    if not check_relation_exists(conn, 'customer_analytics', 'r'):
        print("  [FAIL] Table 'customer_analytics' does not exist")
        return False

    try:
        rows = run_query(conn, "SELECT * FROM customer_analytics LIMIT 1")
        if rows:
            cols = set(rows[0].keys())
            required = {'customer_id', 'full_name', 'email', 'country', 'total_spent',
                        'num_purchases', 'avg_purchase', 'first_purchase', 'last_purchase',
                        'customer_segment'}
            missing = required - cols
            if missing:
                print(f"  [FAIL] Missing columns: {missing}")
                return False
            print("  [PASS] customer_analytics exists with all required columns")
            return True
        else:
            print("  [FAIL] customer_analytics is empty")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


# ============================================================
# Step 4: customer_analytics segmentation correctness
# ============================================================
def verify_customer_segments(conn) -> bool:
    all_ok = True

    # Count customers in each segment
    segments = run_query(conn, """
        SELECT customer_segment, COUNT(*) as cnt 
        FROM customer_analytics 
        GROUP BY customer_segment 
        ORDER BY customer_segment
    """)
    seg_map = {s['customer_segment']: s['cnt'] for s in segments}

    # Compute expected from Invoice table
    expected = run_query(conn, """
        SELECT segment, COUNT(*) as cnt
        FROM (
            SELECT 
                CASE 
                    WHEN "Total" > 45.00 THEN 'VIP'
                    WHEN "Total" >= 25.00 THEN 'Regular'
                    ELSE 'Occasional'
                END as segment
            FROM (
                SELECT "CustomerId", SUM("Total") as "Total"
                FROM "Invoice"
                GROUP BY "CustomerId"
            ) sub
        ) seg_sub
        GROUP BY segment
    """)
    expected_map = {e['segment']: e['cnt'] for e in expected}

    for seg in ['VIP', 'Regular', 'Occasional']:
        actual = seg_map.get(seg, 0)
        exp = expected_map.get(seg, 0)
        if actual == exp:
            print(f"    [PASS] Segment '{seg}': {actual} customers (correct)")
        else:
            print(f"    [FAIL] Segment '{seg}': got {actual}, expected {exp}")
            all_ok = False

    # Check total count
    total_actual = run_scalar(conn, "SELECT COUNT(*) FROM customer_analytics")
    total_expected = run_scalar(conn, 'SELECT COUNT(DISTINCT "CustomerId") FROM "Invoice"')
    if total_actual == total_expected:
        print(f"    [PASS] Total customers: {total_actual}")
    else:
        print(f"    [FAIL] Total: got {total_actual}, expected {total_expected}")
        all_ok = False

    return all_ok


# ============================================================
# Step 5: customer_analytics spot-check values
# ============================================================
def verify_customer_values(conn) -> bool:
    all_ok = True

    # Pick customer 1 as test
    expected = run_query(conn, """
        SELECT 
            "CustomerId" as cid,
            ROUND(SUM("Total")::numeric, 2) as total,
            COUNT(*) as cnt,
            ROUND(AVG("Total")::numeric, 2) as avg_val,
            MIN("InvoiceDate")::date as first_d,
            MAX("InvoiceDate")::date as last_d
        FROM "Invoice"
        WHERE "CustomerId" = 1
        GROUP BY "CustomerId"
    """)

    if not expected:
        print("  [SKIP] Customer 1 has no invoices")
        return True

    exp = expected[0]
    actual = run_query(conn, "SELECT * FROM customer_analytics WHERE customer_id = 1")

    if not actual:
        print("  [FAIL] Customer 1 not found in customer_analytics")
        return False

    act = actual[0]

    # Check total_spent
    if abs(float(act['total_spent']) - float(exp['total'])) < 0.02:
        print(f"    [PASS] Customer 1 total_spent: {act['total_spent']}")
    else:
        print(f"    [FAIL] Customer 1 total_spent: got {act['total_spent']}, expected {exp['total']}")
        all_ok = False

    # Check num_purchases
    if act['num_purchases'] == exp['cnt']:
        print(f"    [PASS] Customer 1 num_purchases: {act['num_purchases']}")
    else:
        print(f"    [FAIL] Customer 1 num_purchases: got {act['num_purchases']}, expected {exp['cnt']}")
        all_ok = False

    return all_ok


# ============================================================
# Step 6: genre_country_rankings exists and has correct structure
# ============================================================
def verify_genre_rankings_exists(conn) -> bool:
    if not check_relation_exists(conn, 'genre_country_rankings', 'r'):
        print("  [FAIL] Table 'genre_country_rankings' does not exist")
        return False

    try:
        rows = run_query(conn, "SELECT * FROM genre_country_rankings LIMIT 1")
        if rows:
            cols = set(rows[0].keys())
            required = {'country', 'genre_name', 'genre_revenue', 'country_rank'}
            missing = required - cols
            if missing:
                print(f"  [FAIL] Missing columns: {missing}")
                return False
            print("  [PASS] genre_country_rankings exists with correct columns")
            return True
        else:
            print("  [FAIL] genre_country_rankings is empty")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


# ============================================================
# Step 7: genre_country_rankings — only top 3 per country
# ============================================================
def verify_genre_rankings_data(conn) -> bool:
    all_ok = True

    # Check max rank
    max_rank = run_scalar(conn, "SELECT MAX(country_rank) FROM genre_country_rankings")
    if max_rank and max_rank <= 3:
        print(f"  [PASS] Max rank is {max_rank} (<= 3)")
    else:
        print(f"  [FAIL] Max rank is {max_rank} (expected <= 3)")
        all_ok = False

    # Check number of countries matches
    expected_countries = run_scalar(conn, 'SELECT COUNT(DISTINCT "BillingCountry") FROM "Invoice"')
    actual_countries = run_scalar(conn, "SELECT COUNT(DISTINCT country) FROM genre_country_rankings")

    if actual_countries == expected_countries:
        print(f"  [PASS] {actual_countries} countries (matches Invoice data)")
    else:
        print(f"  [WARN] {actual_countries} countries in rankings vs {expected_countries} in Invoice")

    # Spot-check USA top genre
    usa_top = run_query(conn, """
        SELECT genre_name, genre_revenue FROM genre_country_rankings 
        WHERE country = 'USA' AND country_rank = 1
    """)

    # Compute expected
    expected_usa_top = run_query(conn, """
        SELECT g."Name" as genre_name, 
               ROUND(SUM(il."UnitPrice" * il."Quantity")::numeric, 2) as revenue
        FROM "Invoice" i
        JOIN "InvoiceLine" il ON il."InvoiceId" = i."InvoiceId"
        JOIN "Track" t ON t."TrackId" = il."TrackId"
        JOIN "Genre" g ON g."GenreId" = t."GenreId"
        WHERE i."BillingCountry" = 'USA'
        GROUP BY g."Name"
        ORDER BY revenue DESC
        LIMIT 1
    """)

    if usa_top and expected_usa_top:
        if usa_top[0]['genre_name'] == expected_usa_top[0]['genre_name']:
            print(f"  [PASS] USA top genre: {usa_top[0]['genre_name']}")
        else:
            print(f"  [FAIL] USA top genre: got '{usa_top[0]['genre_name']}', expected '{expected_usa_top[0]['genre_name']}'")
            all_ok = False
    elif not usa_top:
        print("  [FAIL] No USA data in genre_country_rankings")
        all_ok = False

    return all_ok


# ============================================================
# Step 8: get_customer_top_genre function exists
# ============================================================
def verify_function_exists(conn) -> bool:
    result = run_scalar(conn, """
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE p.proname = 'get_customer_top_genre' AND n.nspname = 'public'
    """)
    if result:
        print("  [PASS] Function 'get_customer_top_genre' exists")
        return True
    else:
        print("  [FAIL] Function 'get_customer_top_genre' not found")
        return False


# ============================================================
# Step 9: get_customer_top_genre returns correct values
# ============================================================
def verify_function_output(conn) -> bool:
    all_ok = True

    # Test with customer 1
    actual = run_scalar(conn, "SELECT get_customer_top_genre(1)")

    # Compute expected
    expected = run_scalar(conn, """
        SELECT g."Name"
        FROM "Invoice" i
        JOIN "InvoiceLine" il ON il."InvoiceId" = i."InvoiceId"
        JOIN "Track" t ON t."TrackId" = il."TrackId"
        JOIN "Genre" g ON g."GenreId" = t."GenreId"
        WHERE i."CustomerId" = 1
        GROUP BY g."Name"
        ORDER BY SUM(il."UnitPrice" * il."Quantity") DESC
        LIMIT 1
    """)

    if actual and expected:
        if actual == expected:
            print(f"    [PASS] Customer 1 top genre: '{actual}'")
        else:
            # Check if it's a valid tie
            top_genres = run_query(conn, """
                SELECT g."Name", SUM(il."UnitPrice" * il."Quantity") as total
                FROM "Invoice" i
                JOIN "InvoiceLine" il ON il."InvoiceId" = i."InvoiceId"
                JOIN "Track" t ON t."TrackId" = il."TrackId"
                JOIN "Genre" g ON g."GenreId" = t."GenreId"
                WHERE i."CustomerId" = 1
                GROUP BY g."Name"
                ORDER BY total DESC
                LIMIT 2
            """)
            if len(top_genres) >= 2 and float(top_genres[0]['total']) == float(top_genres[1]['total']):
                print(f"    [PASS] Customer 1 top genre: '{actual}' (valid tie)")
            else:
                print(f"    [FAIL] Customer 1 top genre: got '{actual}', expected '{expected}'")
                all_ok = False

    # Test edge case: non-existent customer (very high ID)
    no_purchase = run_scalar(conn, "SELECT get_customer_top_genre(99999)")
    if no_purchase and 'no purchase' in no_purchase.lower():
        print(f"    [PASS] Non-existent customer returns: '{no_purchase}'")
    else:
        print(f"    [FAIL] Non-existent customer should return 'No purchases', got: '{no_purchase}'")
        all_ok = False

    return all_ok


# ============================================================
# Step 10: Audit trigger exists
# ============================================================
def verify_trigger_exists(conn) -> bool:
    all_ok = True

    # Check audit log table
    if check_relation_exists(conn, 'customer_audit_log', 'r'):
        print("  [PASS] Table 'customer_audit_log' exists")
    else:
        print("  [FAIL] Table 'customer_audit_log' not found")
        return False

    # Check trigger on Customer
    trigger = run_scalar(conn, """
        SELECT 1 FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        WHERE c.relname = 'Customer' AND NOT t.tgisinternal
    """)

    if trigger:
        print("  [PASS] Trigger on Customer table exists")
    else:
        print("  [FAIL] No trigger found on Customer table")
        all_ok = False

    # Check trigger function
    func = run_scalar(conn, """
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE p.proname = 'fn_customer_audit' AND n.nspname = 'public'
    """)
    if func:
        print("  [PASS] Trigger function 'fn_customer_audit' exists")
    else:
        # Accept any audit-related function name
        func2 = run_scalar(conn, """
            SELECT p.proname FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            JOIN pg_trigger t ON t.tgfoid = p.oid
            JOIN pg_class c ON c.oid = t.tgrelid
            WHERE c.relname = 'Customer' AND n.nspname = 'public'
        """)
        if func2:
            print(f"  [WARN] Found audit function '{func2}' (expected 'fn_customer_audit')")
        else:
            print("  [FAIL] No audit trigger function found")
            all_ok = False

    return all_ok


# ============================================================
# Step 11: Audit trigger fires correctly
# ============================================================
def verify_trigger_fires(conn) -> bool:
    all_ok = True

    try:
        # Clear any previous test data
        with conn.cursor() as cur:
            cur.execute("DELETE FROM customer_audit_log WHERE customer_id = 99998")
            cur.execute("""
                DELETE FROM "Customer" WHERE "CustomerId" = 99998
            """)

        # INSERT test
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "Customer" ("CustomerId", "FirstName", "LastName", "Email")
                VALUES (99998, 'Test', 'Verify', 'test.verify@example.com')
            """)

        insert_log = run_query(conn, """
            SELECT action, customer_id, new_data FROM customer_audit_log 
            WHERE customer_id = 99998 AND action = 'INSERT'
        """)
        if insert_log:
            print("    [PASS] INSERT trigger fired")
        else:
            print("    [FAIL] INSERT trigger did not fire")
            all_ok = False

        # UPDATE test
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "Customer" SET "FirstName" = 'TestUpdated'
                WHERE "CustomerId" = 99998
            """)

        update_log = run_query(conn, """
            SELECT action FROM customer_audit_log 
            WHERE customer_id = 99998 AND action = 'UPDATE'
        """)
        if update_log:
            print("    [PASS] UPDATE trigger fired")
        else:
            print("    [FAIL] UPDATE trigger did not fire")
            all_ok = False

        # DELETE test
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM "Customer" WHERE "CustomerId" = 99998
            """)

        delete_log = run_query(conn, """
            SELECT action FROM customer_audit_log 
            WHERE customer_id = 99998 AND action = 'DELETE'
        """)
        if delete_log:
            print("    [PASS] DELETE trigger fired")
        else:
            print("    [FAIL] DELETE trigger did not fire")
            all_ok = False

        # Cleanup
        with conn.cursor() as cur:
            cur.execute("DELETE FROM customer_audit_log WHERE customer_id = 99998")

    except Exception as e:
        print(f"    [FAIL] Trigger test error: {e}")
        all_ok = False

    return all_ok


# ============================================================
# Step 12: Indexes exist
# ============================================================
def verify_indexes(conn) -> bool:
    all_ok = True
    required_indexes = [
        "idx_invoice_customer",
        "idx_invoiceline_track",
        "idx_customer_analytics_segment",
        "idx_genre_country_rank",
    ]

    for idx_name in required_indexes:
        exists = run_scalar(conn, """
            SELECT 1 FROM pg_indexes WHERE indexname = %s
        """, (idx_name,))
        if exists:
            print(f"    [PASS] Index '{idx_name}' exists")
        else:
            print(f"    [FAIL] Index '{idx_name}' not found")
            all_ok = False

    return all_ok


# ============================================================
# Main
# ============================================================
def main():
    conn = get_conn()
    conn.autocommit = True

    print("Verifying Customer Analytics Pipeline (Chinook DB)")

    steps = [
        ("Step 1: monthly_revenue materialized view exists", lambda: verify_matview_exists(conn)),
        ("Step 2: monthly_revenue data correctness", lambda: verify_matview_data(conn)),
        ("Step 3: customer_analytics table exists", lambda: verify_customer_analytics_exists(conn)),
        ("Step 4: customer_analytics segmentation", lambda: verify_customer_segments(conn)),
        ("Step 5: customer_analytics values spot-check", lambda: verify_customer_values(conn)),
        ("Step 6: genre_country_rankings exists", lambda: verify_genre_rankings_exists(conn)),
        ("Step 7: genre_country_rankings data", lambda: verify_genre_rankings_data(conn)),
        ("Step 8: get_customer_top_genre function exists", lambda: verify_function_exists(conn)),
        ("Step 9: get_customer_top_genre output", lambda: verify_function_output(conn)),
        ("Step 10: Audit trigger exists", lambda: verify_trigger_exists(conn)),
        ("Step 11: Audit trigger fires", lambda: verify_trigger_fires(conn)),
        ("Step 12: Indexes exist", lambda: verify_indexes(conn)),
    ]

    results = []
    for step_name, verify_func in steps:
        print(f"\n{'=' * 55}")
        print(f"  {step_name}")
        print(f"{'=' * 55}")
        try:
            passed = verify_func()
            results.append((step_name, passed))
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append((step_name, False))

    conn.close()

    print(f"\n{'=' * 55}")
    print("  VERIFICATION SUMMARY")
    print(f"{'=' * 55}")
    for step_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {step_name}")

    passed_count = sum(1 for _, p in results if p)
    print(f"\n  Result: {passed_count}/{len(results)} steps passed")

    if all(p for _, p in results):
        print("\n  OVERALL: ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n  OVERALL: SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
