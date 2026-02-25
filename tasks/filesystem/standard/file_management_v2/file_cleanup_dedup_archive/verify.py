#!/usr/bin/env python3
"""
Verification script for Advanced File Cleanup, Dedup & Archive Task (v2)
12 verification steps covering directory structure, file routing, dedup,
JSON validation, report generation, and content integrity.
"""

import sys
import os
import json
from pathlib import Path


def get_test_directory() -> Path:
    """Get the test directory from FILESYSTEM_TEST_DIR env var."""
    test_root = os.environ.get("FILESYSTEM_TEST_DIR")
    if not test_root:
        raise ValueError("FILESYSTEM_TEST_DIR environment variable is required")
    return Path(test_root)


# ==========================================================
# Step 1: Directory Structure
# ==========================================================
def verify_directory_structure(test_dir: Path) -> bool:
    """organized/{csv,json,txt}/, drafts/, quarantine/ must exist."""
    required = [
        "organized",
        "organized/csv",
        "organized/json",
        "organized/txt",
        "drafts",
        "quarantine",
    ]
    all_ok = True
    for d in required:
        p = test_dir / d
        if p.is_dir():
            print(f"  [PASS] Directory '{d}/' exists")
        else:
            print(f"  [FAIL] Directory '{d}/' missing")
            all_ok = False
    return all_ok


# ==========================================================
# Step 2: CSV Files Organized Correctly
# ==========================================================
def verify_csv_organized(test_dir: Path) -> bool:
    """organized/csv/ should have exactly 4 unique CSV files."""
    csv_dir = test_dir / "organized" / "csv"
    if not csv_dir.is_dir():
        print("  [FAIL] organized/csv/ not found")
        return False

    files = sorted([f.name for f in csv_dir.iterdir() if f.is_file()])
    if len(files) != 4:
        print(f"  [FAIL] Expected 4 CSV files, found {len(files)}: {files}")
        return False

    print(f"  [PASS] organized/csv/ has 4 files: {files}")

    # Verify by content markers (not filenames, since model may name differently)
    expected_markers = {
        "q1_sales": "Widget A",
        "server_metrics": "cpu_usage",
        "team_contacts": "alice.chen",
        "sales_data_final": "Acme Corp",
    }

    all_ok = True
    found = set()
    for f in csv_dir.iterdir():
        if f.is_file():
            content = f.read_text(encoding="utf-8", errors="replace").lower()
            for key, marker in expected_markers.items():
                if marker.lower() in content:
                    found.add(key)

    for key in expected_markers:
        if key in found:
            print(f"    [PASS] Found '{key}' content")
        else:
            print(f"    [FAIL] Missing '{key}' content")
            all_ok = False

    return all_ok


# ==========================================================
# Step 3: JSON Files Organized Correctly
# ==========================================================
def verify_json_organized(test_dir: Path) -> bool:
    """organized/json/ should have exactly 4 valid JSON files."""
    json_dir = test_dir / "organized" / "json"
    if not json_dir.is_dir():
        print("  [FAIL] organized/json/ not found")
        return False

    files = sorted([f.name for f in json_dir.iterdir() if f.is_file()])
    if len(files) != 4:
        print(f"  [FAIL] Expected 4 JSON files, found {len(files)}: {files}")
        return False

    print(f"  [PASS] organized/json/ has 4 files: {files}")

    # All files must be valid JSON
    all_ok = True
    for f in json_dir.iterdir():
        if f.is_file():
            try:
                content = f.read_text(encoding="utf-8")
                json.loads(content)
                print(f"    [PASS] {f.name} is valid JSON")
            except json.JSONDecodeError:
                print(f"    [FAIL] {f.name} is NOT valid JSON (should not be in organized/)")
                all_ok = False

    # Verify expected content
    expected_markers = {
        "config": "DataPipeline",
        "api_endpoints": "api.company.com",
        "project_timeline": "Platform Migration",
        "backup_config": "company-backups-prod",
    }

    found = set()
    for f in json_dir.iterdir():
        if f.is_file():
            content = f.read_text(encoding="utf-8", errors="replace")
            for key, marker in expected_markers.items():
                if marker in content:
                    found.add(key)

    for key in expected_markers:
        if key in found:
            print(f"    [PASS] Found '{key}' content")
        else:
            print(f"    [FAIL] Missing '{key}' content")
            all_ok = False

    return all_ok


# ==========================================================
# Step 4: TXT Files Organized Correctly
# ==========================================================
def verify_txt_organized(test_dir: Path) -> bool:
    """organized/txt/ should have exactly 3 non-draft, non-empty TXT files."""
    txt_dir = test_dir / "organized" / "txt"
    if not txt_dir.is_dir():
        print("  [FAIL] organized/txt/ not found")
        return False

    files = sorted([f.name for f in txt_dir.iterdir() if f.is_file()])
    if len(files) != 3:
        print(f"  [FAIL] Expected 3 TXT files, found {len(files)}: {files}")
        return False

    print(f"  [PASS] organized/txt/ has 3 files: {files}")

    expected_markers = {
        "meeting_notes": "January 2026 Planning",
        "error_log": "DatabaseConnection",
        "weekly_summary": "Weekly Summary",
    }

    all_ok = True
    found = set()
    for f in txt_dir.iterdir():
        if f.is_file():
            content = f.read_text(encoding="utf-8", errors="replace")
            for key, marker in expected_markers.items():
                if marker in content:
                    found.add(key)

    for key in expected_markers:
        if key in found:
            print(f"    [PASS] Found '{key}' content")
        else:
            print(f"    [FAIL] Missing '{key}' content")
            all_ok = False

    return all_ok


# ==========================================================
# Step 5: Drafts Separated
# ==========================================================
def verify_drafts(test_dir: Path) -> bool:
    """drafts/ should contain exactly 2 draft files."""
    drafts_dir = test_dir / "drafts"
    if not drafts_dir.is_dir():
        print("  [FAIL] drafts/ not found")
        return False

    files = sorted([f.name for f in drafts_dir.iterdir() if f.is_file()])
    if len(files) != 2:
        print(f"  [FAIL] Expected 2 draft files, found {len(files)}: {files}")
        return False

    print(f"  [PASS] drafts/ has 2 files: {files}")

    # Verify content
    all_ok = True
    all_content = ""
    for f in drafts_dir.iterdir():
        if f.is_file():
            all_content += f.read_text(encoding="utf-8", errors="replace")

    if "Budget Proposal" in all_content or "budget" in all_content.lower():
        print("    [PASS] Budget proposal draft found")
    else:
        print("    [FAIL] Budget proposal draft missing")
        all_ok = False

    if "Code Review" in all_content or "review guidelines" in all_content.lower():
        print("    [PASS] Review guidelines draft found")
    else:
        print("    [FAIL] Review guidelines draft missing")
        all_ok = False

    return all_ok


# ==========================================================
# Step 6: Malformed JSON Quarantined
# ==========================================================
def verify_quarantine(test_dir: Path) -> bool:
    """quarantine/ should have exactly 2 malformed JSON files."""
    q_dir = test_dir / "quarantine"
    if not q_dir.is_dir():
        print("  [FAIL] quarantine/ not found")
        return False

    files = sorted([f.name for f in q_dir.iterdir() if f.is_file()])
    if len(files) != 2:
        print(f"  [FAIL] Expected 2 quarantined files, found {len(files)}: {files}")
        return False

    print(f"  [PASS] quarantine/ has 2 files: {files}")

    # Check content markers
    all_ok = True
    all_content = ""
    for f in q_dir.iterdir():
        if f.is_file():
            all_content += f.read_text(encoding="utf-8", errors="replace")

    if "EXP-2026-042" in all_content or "gradient_boost" in all_content:
        print("    [PASS] analysis_results found in quarantine")
    else:
        print("    [FAIL] analysis_results missing from quarantine")
        all_ok = False

    if "legacy_database" in all_content or "EXP-20260201" in all_content:
        print("    [PASS] broken_export found in quarantine")
    else:
        print("    [FAIL] broken_export missing from quarantine")
        all_ok = False

    # Check .invalid extension on at least one file
    has_invalid_ext = any(".invalid" in f.name for f in q_dir.iterdir() if f.is_file())
    if has_invalid_ext:
        print("    [PASS] At least one file has .invalid extension")
    else:
        print("    [WARN] No .invalid extension found (minor format issue)")
        # Not a hard fail - content placement is more important

    return all_ok


# ==========================================================
# Step 7: Empty Files Handled
# ==========================================================
def verify_empty_files_handled(test_dir: Path) -> bool:
    """Empty files should be in trash/ or effectively removed, NOT in organized/ or drafts/."""
    all_ok = True

    # Empty files: old_scratch.txt and temp_notes.txt
    # Must NOT appear in organized/ or drafts/ directories
    protected_dirs = [
        test_dir / "organized" / "csv",
        test_dir / "organized" / "json",
        test_dir / "organized" / "txt",
        test_dir / "drafts",
    ]

    empty_file_markers = ["old_scratch", "temp_notes"]

    for marker in empty_file_markers:
        found_in_protected = False
        for pd in protected_dirs:
            if pd.is_dir():
                for f in pd.iterdir():
                    if marker in f.name.lower():
                        found_in_protected = True
                        print(f"    [FAIL] Empty file '{marker}' found in {pd.relative_to(test_dir)}")
                        break

        if found_in_protected:
            all_ok = False
            continue

        # Check if in trash/ (preferred) or otherwise handled
        trash_dir = test_dir / "trash"
        if trash_dir.is_dir():
            in_trash = any(marker in f.name.lower() for f in trash_dir.iterdir() if f.is_file())
            if in_trash:
                print(f"    [PASS] '{marker}' moved to trash/")
                continue

        # Also acceptable: file deleted entirely or emptied
        print(f"    [PASS] '{marker}' not in organized/drafts dirs (acceptable handling)")

    return all_ok


# ==========================================================
# Step 8: Non-Target Files Preserved
# ==========================================================
def verify_preserved_files(test_dir: Path) -> bool:
    """README.md and project_overview.md must remain untouched."""
    all_ok = True

    # shared/README.md
    readme = test_dir / "shared" / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8")
        if "Shared Workspace" in content:
            print("  [PASS] shared/README.md preserved with correct content")
        else:
            print("  [FAIL] shared/README.md content was modified")
            all_ok = False
    else:
        print("  [FAIL] shared/README.md missing")
        all_ok = False

    # project_overview.md (root)
    overview = test_dir / "project_overview.md"
    if overview.is_file():
        content = overview.read_text(encoding="utf-8")
        if "Platform Migration" in content:
            print("  [PASS] project_overview.md preserved with correct content")
        else:
            print("  [FAIL] project_overview.md content was modified")
            all_ok = False
    else:
        print("  [FAIL] project_overview.md missing")
        all_ok = False

    return all_ok


# ==========================================================
# Step 9: No Duplicate Content in Organized
# ==========================================================
def verify_no_duplicates_in_organized(test_dir: Path) -> bool:
    """No two files in organized/ should have identical content."""
    organized_dir = test_dir / "organized"
    if not organized_dir.is_dir():
        print("  [FAIL] organized/ not found")
        return False

    all_ok = True

    # Collect all file contents in organized/
    file_contents = {}
    for subdir in ["csv", "json", "txt"]:
        sd = organized_dir / subdir
        if sd.is_dir():
            for f in sd.iterdir():
                if f.is_file():
                    content = f.read_text(encoding="utf-8", errors="replace").strip()
                    # Use content hash (first 500 chars for efficiency)
                    content_key = content[:500]
                    if content_key in file_contents:
                        print(f"  [FAIL] Duplicate content: '{f.name}' and '{file_contents[content_key]}' have identical content")
                        all_ok = False
                    else:
                        file_contents[content_key] = f.name

    if all_ok:
        print("  [PASS] No duplicate content in organized/")

    return all_ok


# ==========================================================
# Step 10: Inventory Report
# ==========================================================
def verify_inventory_report(test_dir: Path) -> bool:
    """inventory.md should exist and accurately list organized files."""
    inv = test_dir / "inventory.md"
    if not inv.is_file():
        print("  [FAIL] inventory.md not found")
        return False

    content = inv.read_text(encoding="utf-8")
    content_lower = content.lower()

    all_ok = True

    # Must mention all three categories
    for cat in ["csv", "json", "txt"]:
        if cat in content_lower:
            print(f"    [PASS] inventory.md mentions '{cat}' category")
        else:
            print(f"    [FAIL] inventory.md missing '{cat}' category")
            all_ok = False

    # Must mention key organized files (at least 8 out of 11)
    expected_files = [
        "server_metrics", "team_contacts", "sales_data",
        "config", "api_endpoints", "project_timeline", "backup_config",
        "meeting_notes", "error_log", "weekly_summary",
    ]

    found_count = 0
    for ef in expected_files:
        if ef in content_lower:
            found_count += 1

    if found_count >= 8:
        print(f"    [PASS] inventory mentions {found_count}/10 expected files")
    else:
        print(f"    [FAIL] inventory only mentions {found_count}/10 expected files")
        all_ok = False

    # Should include file sizes (KB)
    if "kb" in content_lower:
        print("    [PASS] inventory includes file sizes")
    else:
        print("    [FAIL] inventory missing file sizes")
        all_ok = False

    return all_ok


# ==========================================================
# Step 11: Duplicates Report
# ==========================================================
def verify_duplicates_report(test_dir: Path) -> bool:
    """duplicates_report.md should document detected duplicates."""
    # Try several possible filenames
    candidates = [
        "duplicates_report.md",
        "duplicate_report.md",
        "duplicates.md",
    ]
    dup = None
    for c in candidates:
        p = test_dir / c
        if p.is_file():
            dup = p
            break

    if dup is None:
        print("  [FAIL] duplicates_report.md (or similar) not found")
        return False

    content = dup.read_text(encoding="utf-8")
    content_lower = content.lower()

    all_ok = True

    # Must mention the Q1 sales duplicate
    q1_mentioned = any(kw in content_lower for kw in [
        "q1_sales", "sales_report", "sales_backup"
    ])
    if q1_mentioned:
        print("    [PASS] Mentions Q1 sales duplicate")
    else:
        print("    [FAIL] Missing Q1 sales duplicate mention")
        all_ok = False

    # Must mention the server metrics duplicate
    metrics_mentioned = any(kw in content_lower for kw in [
        "server_metrics", "server metrics"
    ])
    if metrics_mentioned:
        print("    [PASS] Mentions server metrics duplicate")
    else:
        print("    [FAIL] Missing server metrics duplicate mention")
        all_ok = False

    # Must use the word "duplicate"
    if "duplicate" in content_lower:
        print("    [PASS] Report discusses duplicates")
    else:
        print("    [FAIL] Report doesn't mention 'duplicate'")
        all_ok = False

    return all_ok


# ==========================================================
# Step 12: Audit Summary
# ==========================================================
def verify_audit_summary(test_dir: Path) -> bool:
    """audit_summary.md should contain correct processing statistics."""
    candidates = [
        "audit_summary.md",
        "audit.md",
        "summary.md",
        "processing_summary.md",
    ]
    audit = None
    for c in candidates:
        p = test_dir / c
        if p.is_file():
            audit = p
            break

    if audit is None:
        print("  [FAIL] audit_summary.md (or similar) not found")
        return False

    content = audit.read_text(encoding="utf-8")
    content_lower = content.lower()

    all_ok = True

    # Must mention key categories of processing
    required_mentions = {
        "organized": ["organized", "organiz"],
        "duplicate": ["duplicate", "dedup"],
        "quarantine": ["quarantine", "malformed", "invalid"],
        "draft": ["draft"],
        "empty": ["empty", "discard", "trash"],
    }

    for category, keywords in required_mentions.items():
        if any(kw in content_lower for kw in keywords):
            print(f"    [PASS] Audit mentions '{category}' processing")
        else:
            print(f"    [FAIL] Audit missing '{category}' processing mention")
            all_ok = False

    # Check for expected numbers (flexible — check if key numbers appear)
    # 11 organized, 2 duplicates, 2 quarantined, 2 drafts, 2 empty
    # Total scanned: 19 target files
    numbers_in_content = set()
    import re
    for match in re.finditer(r'\b(\d+)\b', content):
        numbers_in_content.add(int(match.group(1)))

    # At minimum, some key numbers should appear
    if 11 in numbers_in_content:
        print("    [PASS] Mentions 11 (files organized)")
    else:
        print("    [WARN] Expected '11' (files organized) — model may count differently")

    if 2 in numbers_in_content:
        print("    [PASS] Mentions 2 (appears in expected counts)")
    else:
        print("    [WARN] Expected '2' to appear (duplicates/quarantined/drafts/empty)")

    return all_ok


# ==========================================================
# Main
# ==========================================================
def main():
    test_dir = get_test_directory()

    print(f"Test directory: {test_dir}")
    print(f"Directory exists: {test_dir.is_dir()}")

    verification_steps = [
        ("Step 1: Directory Structure", verify_directory_structure),
        ("Step 2: CSV Files Organized", verify_csv_organized),
        ("Step 3: JSON Files Organized", verify_json_organized),
        ("Step 4: TXT Files Organized", verify_txt_organized),
        ("Step 5: Drafts Separated", verify_drafts),
        ("Step 6: Malformed JSON Quarantined", verify_quarantine),
        ("Step 7: Empty Files Handled", verify_empty_files_handled),
        ("Step 8: Non-Target Files Preserved", verify_preserved_files),
        ("Step 9: No Duplicates in Organized", verify_no_duplicates_in_organized),
        ("Step 10: Inventory Report", verify_inventory_report),
        ("Step 11: Duplicates Report", verify_duplicates_report),
        ("Step 12: Audit Summary", verify_audit_summary),
    ]

    all_passed = True
    results = []

    for step_name, verify_func in verification_steps:
        print(f"\n{'='*55}")
        print(f"  {step_name}")
        print(f"{'='*55}")
        try:
            passed = verify_func(test_dir)
            results.append((step_name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            results.append((step_name, False))
            all_passed = False

    # Summary
    print(f"\n{'='*55}")
    print("  VERIFICATION SUMMARY")
    print(f"{'='*55}")
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
