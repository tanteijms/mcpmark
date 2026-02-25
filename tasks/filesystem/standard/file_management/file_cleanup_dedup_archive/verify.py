#!/usr/bin/env python3
"""
Verification for Advanced File Cleanup v3 (L3+)
15 strict checks. Target: no model passes 4/4.

Ground truth (33 files total):
  organized/csv/: 9 files (q1_sales_report, q1_sales_report_v2, server_metrics,
                           daily_report_jan15, daily_report_feb03, quarterly_forecast,
                           team_contacts, department_budgets, sales_data_final)
  organized/json/: 5 files (config_v2, summary_stats, api_endpoints,
                            project_timeline, backup_config)
  organized/txt/: 4 files (meeting_notes_jan, error_log, weekly_summary, old_meeting_notes)
  drafts/: 4 files (draft_budget_proposal, draft_review, draft_roadmap, draft_proposal_v1)
  quarantine/: 3 files (analysis_results.json.invalid, broken_export.json.invalid,
                        legacy_config.json.invalid)
  trash/: 3 files (old_scratch.txt, temp_notes.txt, DRAFT_empty.txt)
  duplicates removed: 2 (q1_sales_backup.csv, Server Metrics.csv)
  preserved: 3 (README.md, project_overview.md, .gitignore)
"""

import sys
import os
import json
import re
from pathlib import Path


def get_test_directory() -> Path:
    test_root = os.environ.get("FILESYSTEM_TEST_DIR")
    if not test_root:
        raise ValueError("FILESYSTEM_TEST_DIR environment variable is required")
    return Path(test_root)


# ============================================================
# Step 1: Directory Structure
# ============================================================
def verify_directory_structure(test_dir: Path) -> bool:
    required = [
        "organized", "organized/csv", "organized/json", "organized/txt",
        "drafts", "quarantine",
    ]
    all_ok = True
    for d in required:
        if not (test_dir / d).is_dir():
            print(f"  [FAIL] Directory '{d}/' missing")
            all_ok = False
    if all_ok:
        print("  [PASS] All required directories exist")
    return all_ok


# ============================================================
# Step 2: CSV count EXACTLY 9
# ============================================================
def verify_csv_count(test_dir: Path) -> bool:
    csv_dir = test_dir / "organized" / "csv"
    if not csv_dir.is_dir():
        print("  [FAIL] organized/csv/ not found")
        return False
    files = [f for f in csv_dir.iterdir() if f.is_file()]
    if len(files) == 9:
        print(f"  [PASS] organized/csv/ has exactly 9 files")
        return True
    else:
        print(f"  [FAIL] organized/csv/ has {len(files)} files, expected 9: {sorted(f.name for f in files)}")
        return False


# ============================================================
# Step 3: CSV content verification (all 9 present)
# ============================================================
def verify_csv_content(test_dir: Path) -> bool:
    csv_dir = test_dir / "organized" / "csv"
    if not csv_dir.is_dir():
        print("  [FAIL] organized/csv/ not found")
        return False

    expected = {
        "q1_sales": ("Widget A", "4500.00"),
        "server_metrics": ("cpu_usage", "memory_mb"),
        "daily_jan15": ("api_latency_p95", "15847"),
        "daily_feb03": ("16203", "82.3"),
        "quarterly_forecast": ("projected_revenue", "variance_pct"),
        "team_contacts": ("alice.chen", "Engineering"),
        "department_budgets": ("Operations", "287100"),
        "sales_data_final": ("Acme Corp", "ORD-001"),
        "q1_v2": ("12400.00", "2026-03-28"),  # the EXTRA row in v2
    }

    all_content = ""
    for f in csv_dir.iterdir():
        if f.is_file():
            all_content += f.read_text(encoding="utf-8", errors="replace")

    all_ok = True
    for key, markers in expected.items():
        found = all(m in all_content for m in markers)
        if found:
            print(f"    [PASS] '{key}' content found")
        else:
            print(f"    [FAIL] '{key}' content missing")
            all_ok = False
    return all_ok


# ============================================================
# Step 4: Near-duplicate KEPT (v2 csv must be in organized)
# ============================================================
def verify_near_duplicate_kept(test_dir: Path) -> bool:
    """Q1_Sales_Report_v2.csv has extra row '2026-03-28,Gadget X,310,12400.00,West'
    It must NOT be treated as a duplicate. Must be in organized/csv/."""
    csv_dir = test_dir / "organized" / "csv"
    if not csv_dir.is_dir():
        print("  [FAIL] organized/csv/ not found")
        return False

    for f in csv_dir.iterdir():
        if f.is_file():
            content = f.read_text(encoding="utf-8", errors="replace")
            if "12400.00" in content and "2026-03-28" in content:
                print(f"  [PASS] Near-duplicate Q1_Sales_Report_v2 found in organized/csv/ as '{f.name}'")
                return True

    print("  [FAIL] Near-duplicate Q1_Sales_Report_v2 (with row '2026-03-28') NOT found in organized/csv/")
    print("         Model likely incorrectly deduped it against Q1_Sales_Report.csv")
    return False


# ============================================================
# Step 5: JSON count EXACTLY 5, all valid
# ============================================================
def verify_json_organized(test_dir: Path) -> bool:
    json_dir = test_dir / "organized" / "json"
    if not json_dir.is_dir():
        print("  [FAIL] organized/json/ not found")
        return False

    files = [f for f in json_dir.iterdir() if f.is_file()]
    if len(files) != 5:
        print(f"  [FAIL] Expected 5 JSON files, found {len(files)}: {sorted(f.name for f in files)}")
        return False
    print(f"  [PASS] organized/json/ has 5 files")

    # All must be valid JSON
    all_ok = True
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"    [FAIL] {f.name} is NOT valid JSON")
            all_ok = False

    # Content markers
    expected = {
        "config": "DataPipeline",
        "summary_stats": "1245000.50",
        "api_endpoints": "api.company.com",
        "project_timeline": "Platform Migration",
        "backup_config": "company-backups-prod",
    }
    all_content = ""
    for f in files:
        all_content += f.read_text(encoding="utf-8", errors="replace")
    for key, marker in expected.items():
        if marker in all_content:
            print(f"    [PASS] '{key}' content found")
        else:
            print(f"    [FAIL] '{key}' content missing")
            all_ok = False
    return all_ok


# ============================================================
# Step 6: TXT count EXACTLY 4
# ============================================================
def verify_txt_organized(test_dir: Path) -> bool:
    txt_dir = test_dir / "organized" / "txt"
    if not txt_dir.is_dir():
        print("  [FAIL] organized/txt/ not found")
        return False

    files = [f for f in txt_dir.iterdir() if f.is_file()]
    if len(files) != 4:
        print(f"  [FAIL] Expected 4 TXT files, found {len(files)}: {sorted(f.name for f in files)}")
        return False
    print(f"  [PASS] organized/txt/ has 4 files")

    expected = {
        "meeting_jan": "January 2026 Planning",
        "error_log": "DatabaseConnection",
        "weekly_summary": "Weekly Summary",
        "old_meeting": "December 2025 Retrospective",
    }
    all_content = ""
    for f in files:
        all_content += f.read_text(encoding="utf-8", errors="replace")
    all_ok = True
    for key, marker in expected.items():
        if marker in all_content:
            print(f"    [PASS] '{key}' content found")
        else:
            print(f"    [FAIL] '{key}' content missing")
            all_ok = False
    return all_ok


# ============================================================
# Step 7: Drafts EXACTLY 4 (non-empty drafts only)
# ============================================================
def verify_drafts(test_dir: Path) -> bool:
    drafts_dir = test_dir / "drafts"
    if not drafts_dir.is_dir():
        print("  [FAIL] drafts/ not found")
        return False

    files = [f for f in drafts_dir.iterdir() if f.is_file()]
    if len(files) != 4:
        print(f"  [FAIL] Expected 4 draft files, found {len(files)}: {sorted(f.name for f in files)}")
        return False
    print(f"  [PASS] drafts/ has 4 files")

    expected_content = ["Budget Proposal", "Code Review", "Roadmap", "Migration Proposal"]
    all_content = ""
    for f in files:
        all_content += f.read_text(encoding="utf-8", errors="replace")
    all_ok = True
    for marker in expected_content:
        if marker in all_content:
            print(f"    [PASS] Draft '{marker}' found")
        else:
            print(f"    [FAIL] Draft '{marker}' missing")
            all_ok = False
    return all_ok


# ============================================================
# Step 8: Quarantine EXACTLY 3 malformed JSONs
# ============================================================
def verify_quarantine(test_dir: Path) -> bool:
    q_dir = test_dir / "quarantine"
    if not q_dir.is_dir():
        print("  [FAIL] quarantine/ not found")
        return False

    files = [f for f in q_dir.iterdir() if f.is_file()]
    if len(files) != 3:
        print(f"  [FAIL] Expected 3 quarantined files, found {len(files)}: {sorted(f.name for f in files)}")
        return False
    print(f"  [PASS] quarantine/ has 3 files")

    all_content = ""
    for f in files:
        all_content += f.read_text(encoding="utf-8", errors="replace")

    all_ok = True
    markers = {
        "analysis_results": "EXP-2026-042",
        "broken_export": "legacy_database",
        "legacy_config": "legacy_service",
    }
    for name, marker in markers.items():
        if marker in all_content:
            print(f"    [PASS] '{name}' in quarantine")
        else:
            print(f"    [FAIL] '{name}' missing from quarantine")
            all_ok = False
    return all_ok


# ============================================================
# Step 9: Priority conflict — DRAFT_empty.txt in trash NOT drafts
# ============================================================
def verify_priority_conflict(test_dir: Path) -> bool:
    """DRAFT_empty.txt is both empty AND has DRAFT in name.
    Rule A (empty→trash) has priority over Rule B (draft→drafts).
    It must NOT be in drafts/."""
    drafts_dir = test_dir / "drafts"

    if drafts_dir.is_dir():
        for f in drafts_dir.iterdir():
            if f.is_file():
                name_lower = f.name.lower()
                if "draft_empty" in name_lower or "empty" in name_lower:
                    content = f.read_text(encoding="utf-8", errors="replace").strip()
                    if len(content) == 0:
                        print("  [FAIL] DRAFT_empty.txt found in drafts/ — it's empty, should be in trash/ (Rule A > Rule B)")
                        return False

    # Check it's properly handled (in trash, deleted, or not in organized)
    organized_dirs = [
        test_dir / "organized" / "csv",
        test_dir / "organized" / "json",
        test_dir / "organized" / "txt",
    ]
    for od in organized_dirs:
        if od.is_dir():
            for f in od.iterdir():
                if "draft_empty" in f.name.lower():
                    print("  [FAIL] DRAFT_empty.txt found in organized/ — it's empty, should be in trash/")
                    return False

    print("  [PASS] DRAFT_empty.txt correctly NOT in drafts/ or organized/ (empty file priority)")
    return True


# ============================================================
# Step 10: No duplicate content in organized/
# ============================================================
def verify_no_duplicates(test_dir: Path) -> bool:
    organized = test_dir / "organized"
    if not organized.is_dir():
        print("  [FAIL] organized/ not found")
        return False

    contents = {}
    all_ok = True
    for subdir in ["csv", "json", "txt"]:
        sd = organized / subdir
        if sd.is_dir():
            for f in sd.iterdir():
                if f.is_file():
                    content = f.read_text(encoding="utf-8", errors="replace").strip()
                    key = content[:300]
                    if key in contents:
                        print(f"  [FAIL] Duplicate content: '{f.name}' matches '{contents[key]}'")
                        all_ok = False
                    else:
                        contents[key] = f.name

    if all_ok:
        print("  [PASS] No duplicate content in organized/")
    return all_ok


# ============================================================
# Step 11: Hidden file + .md files preserved
# ============================================================
def verify_preserved(test_dir: Path) -> bool:
    all_ok = True

    # .gitignore in root
    gitignore = test_dir / ".gitignore"
    if gitignore.is_file():
        content = gitignore.read_text(encoding="utf-8")
        if "__pycache__" in content:
            print("  [PASS] .gitignore preserved")
        else:
            print("  [FAIL] .gitignore content modified")
            all_ok = False
    else:
        print("  [FAIL] .gitignore missing")
        all_ok = False

    # shared/README.md
    readme = test_dir / "shared" / "README.md"
    if readme.is_file() and "Shared Workspace" in readme.read_text(encoding="utf-8"):
        print("  [PASS] shared/README.md preserved")
    else:
        print("  [FAIL] shared/README.md missing or modified")
        all_ok = False

    # project_overview.md
    overview = test_dir / "project_overview.md"
    if overview.is_file() and "Platform Migration" in overview.read_text(encoding="utf-8"):
        print("  [PASS] project_overview.md preserved")
    else:
        print("  [FAIL] project_overview.md missing or modified")
        all_ok = False

    return all_ok


# ============================================================
# Step 12: Inventory report — all 18 organized files listed
# ============================================================
def verify_inventory(test_dir: Path) -> bool:
    inv = test_dir / "inventory.md"
    if not inv.is_file():
        print("  [FAIL] inventory.md not found")
        return False

    content = inv.read_text(encoding="utf-8")
    cl = content.lower()

    all_ok = True

    # Must have all 3 categories
    for cat in ["csv", "json", "txt"]:
        if cat not in cl:
            print(f"  [FAIL] Missing '{cat}' category")
            all_ok = False

    # Must mention key files (check at least 14 of 18)
    expected_files = [
        "q1_sales_report", "q1_sales_report_v2", "server_metrics",
        "daily_report", "quarterly_forecast", "team_contacts",
        "department_budgets", "sales_data",
        "config_v2", "summary_stats", "api_endpoints", "project_timeline",
        "backup_config",
        "meeting_notes", "error_log", "weekly_summary", "old_meeting",
    ]
    found = sum(1 for f in expected_files if f in cl)
    if found >= 14:
        print(f"  [PASS] Inventory mentions {found}/{len(expected_files)} expected files")
    else:
        print(f"  [FAIL] Inventory only mentions {found}/{len(expected_files)} files")
        all_ok = False

    # Must have "kb" (file sizes)
    if "kb" in cl:
        print("  [PASS] File sizes present")
    else:
        print("  [FAIL] File sizes missing")
        all_ok = False

    # Must mention total count
    if "18" in content:
        print("  [PASS] Total count 18 found")
    elif "19" in content:
        print("  [WARN] Total count 19 found (close)")
    else:
        print("  [FAIL] Expected total organized count ~18 not found")
        all_ok = False

    return all_ok


# ============================================================
# Step 13: Duplicates report — mentions both pairs
# ============================================================
def verify_duplicates_report(test_dir: Path) -> bool:
    candidates = ["duplicates_report.md", "duplicate_report.md", "duplicates.md"]
    dup = None
    for c in candidates:
        if (test_dir / c).is_file():
            dup = test_dir / c
            break
    if not dup:
        print("  [FAIL] duplicates_report.md not found")
        return False

    content = dup.read_text(encoding="utf-8").lower()
    all_ok = True

    # Q1 sales duplicate
    if any(kw in content for kw in ["q1_sales", "sales_backup", "sales_report"]):
        print("  [PASS] Q1 sales duplicate mentioned")
    else:
        print("  [FAIL] Q1 sales duplicate not mentioned")
        all_ok = False

    # Server metrics duplicate
    if any(kw in content for kw in ["server_metrics", "server metrics"]):
        print("  [PASS] Server metrics duplicate mentioned")
    else:
        print("  [FAIL] Server metrics duplicate not mentioned")
        all_ok = False

    # Must mention "2" duplicates (exactly 2 pairs)
    if "2" in content and "duplicate" in content:
        print("  [PASS] Reports 2 duplicates")
    else:
        print("  [WARN] Duplicate count may not be exactly 2")

    return all_ok


# ============================================================
# Step 14: Audit summary — correct statistics
# ============================================================
def verify_audit_summary(test_dir: Path) -> bool:
    candidates = ["audit_summary.md", "audit.md", "summary.md"]
    audit = None
    for c in candidates:
        if (test_dir / c).is_file():
            audit = test_dir / c
            break
    if not audit:
        print("  [FAIL] audit_summary.md not found")
        return False

    content = audit.read_text(encoding="utf-8")
    cl = content.lower()

    all_ok = True
    numbers = [int(n) for n in re.findall(r'\b(\d+)\b', content)]

    # Expected: organized=18, duplicates=2, quarantined=3, drafts=4, empty=3, preserved=3
    checks = {
        "organized": (18, ["organized", "organiz"]),
        "quarantined": (3, ["quarantine", "malformed", "invalid"]),
        "drafts": (4, ["draft"]),
        "empty/trash": (3, ["empty", "trash", "discard"]),
    }

    for label, (expected_num, keywords) in checks.items():
        kw_found = any(kw in cl for kw in keywords)
        num_found = expected_num in numbers
        if kw_found and num_found:
            print(f"  [PASS] '{label}' = {expected_num}")
        elif kw_found:
            print(f"  [FAIL] '{label}' mentioned but count {expected_num} not found")
            all_ok = False
        else:
            print(f"  [FAIL] '{label}' not mentioned in audit")
            all_ok = False

    # Check per-type breakdown
    if "csv" in cl and "json" in cl and "txt" in cl:
        print("  [PASS] Per-type breakdown present")
    else:
        print("  [FAIL] Per-type breakdown missing")
        all_ok = False

    return all_ok


# ============================================================
# Step 15: Cross-report consistency
# ============================================================
def verify_cross_consistency(test_dir: Path) -> bool:
    """Numbers across all 3 reports AND actual directories must be consistent."""
    all_ok = True

    # Count actual files in directories
    actual_counts = {}
    for subdir in ["csv", "json", "txt"]:
        sd = test_dir / "organized" / subdir
        if sd.is_dir():
            actual_counts[subdir] = len([f for f in sd.iterdir() if f.is_file()])
        else:
            actual_counts[subdir] = 0

    actual_total = sum(actual_counts.values())
    actual_drafts = 0
    if (test_dir / "drafts").is_dir():
        actual_drafts = len([f for f in (test_dir / "drafts").iterdir() if f.is_file()])
    actual_quarantine = 0
    if (test_dir / "quarantine").is_dir():
        actual_quarantine = len([f for f in (test_dir / "quarantine").iterdir() if f.is_file()])

    # Check inventory file count matches actual
    inv = test_dir / "inventory.md"
    if inv.is_file():
        inv_content = inv.read_text(encoding="utf-8")
        # Count listed files (lines starting with "- ")
        listed_files = len(re.findall(r'^\s*-\s+\S+\.(csv|json|txt)', inv_content, re.MULTILINE | re.IGNORECASE))
        if listed_files == actual_total:
            print(f"  [PASS] Inventory lists {listed_files} files = actual {actual_total}")
        elif abs(listed_files - actual_total) <= 1:
            print(f"  [WARN] Inventory lists {listed_files}, actual is {actual_total} (off by 1)")
        else:
            print(f"  [FAIL] Inventory lists {listed_files} files but actual is {actual_total}")
            all_ok = False

    # Check audit numbers match actual
    candidates = ["audit_summary.md", "audit.md", "summary.md"]
    audit = None
    for c in candidates:
        if (test_dir / c).is_file():
            audit = test_dir / c
            break
    if audit:
        audit_content = audit.read_text(encoding="utf-8")
        audit_numbers = [int(n) for n in re.findall(r'\b(\d+)\b', audit_content)]

        # Check organized total
        if actual_total in audit_numbers:
            print(f"  [PASS] Audit organized count ({actual_total}) matches actual")
        else:
            print(f"  [FAIL] Audit doesn't contain actual organized count {actual_total}")
            all_ok = False

        # Check quarantine count
        if actual_quarantine in audit_numbers:
            print(f"  [PASS] Audit quarantine count ({actual_quarantine}) matches actual")
        else:
            print(f"  [WARN] Audit quarantine count may not match actual ({actual_quarantine})")

    return all_ok


# ============================================================
# Main
# ============================================================
def main():
    test_dir = get_test_directory()
    print(f"Test directory: {test_dir}")

    verification_steps = [
        ("Step 1: Directory Structure", verify_directory_structure),
        ("Step 2: CSV Count (exactly 9)", verify_csv_count),
        ("Step 3: CSV Content Verification", verify_csv_content),
        ("Step 4: Near-Duplicate KEPT", verify_near_duplicate_kept),
        ("Step 5: JSON Organized (exactly 5, all valid)", verify_json_organized),
        ("Step 6: TXT Organized (exactly 4)", verify_txt_organized),
        ("Step 7: Drafts (exactly 4, non-empty only)", verify_drafts),
        ("Step 8: Quarantine (exactly 3 malformed JSONs)", verify_quarantine),
        ("Step 9: Priority Conflict (DRAFT_empty → trash)", verify_priority_conflict),
        ("Step 10: No Duplicate Content in Organized", verify_no_duplicates),
        ("Step 11: Hidden + MD Files Preserved", verify_preserved),
        ("Step 12: Inventory Report", verify_inventory),
        ("Step 13: Duplicates Report", verify_duplicates_report),
        ("Step 14: Audit Summary Statistics", verify_audit_summary),
        ("Step 15: Cross-Report Consistency", verify_cross_consistency),
    ]

    all_passed = True
    results = []

    for step_name, verify_func in verification_steps:
        print(f"\n{'='*58}")
        print(f"  {step_name}")
        print(f"{'='*58}")
        try:
            passed = verify_func(test_dir)
            results.append((step_name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            results.append((step_name, False))
            all_passed = False

    print(f"\n{'='*58}")
    print("  VERIFICATION SUMMARY")
    print(f"{'='*58}")
    for step_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {step_name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n  Result: {passed_count}/{total_count} steps passed")

    if all_passed:
        print("\n  OVERALL: ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n  OVERALL: SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
