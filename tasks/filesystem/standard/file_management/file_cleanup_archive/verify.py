#!/usr/bin/env python3
"""
Verification script for: File Cleanup and Archive
Checks the final state after agent completes the task.
"""

import sys
from pathlib import Path
import os


def get_test_directory() -> Path:
    """Get the test directory from FILESYSTEM_TEST_DIR env var."""
    test_root = os.environ.get("FILESYSTEM_TEST_DIR")
    if not test_root:
        raise ValueError("FILESYSTEM_TEST_DIR environment variable is required")
    return Path(test_root)


# ============================================================
# Expected mappings (ground truth)
# ============================================================
# Original filename -> (target subdir, normalized name)
EXPECTED_MOVES = {
    "Sales Report.csv":    ("csv", "sales_report.csv"),
    "monthly_report.csv":  ("csv", "monthly_report.csv"),
    "Data Export.csv":     ("csv", "data_export.csv"),
    "Config Settings.json":("json", "config_settings.json"),
    "api_response.json":   ("json", "api_response.json"),
    "summary.JSON":        ("json", "summary.json"),
    "USER_LOG.txt":        ("txt", "user_log.txt"),
    "NOTES.txt":           ("txt", "notes.txt"),
    "Meeting Notes.TXT":   ("txt", "meeting_notes.txt"),
}

# Files that should be deleted (empty or whitespace-only)
SHOULD_DELETE = ["empty_file.csv", "blank.txt"]

# Files that should NOT be touched
PRESERVED_FILES = ["README.md"]


# ============================================================
# Check 1: Subdirectories exist
# ============================================================
def verify_subdirectories_exist(test_dir: Path) -> bool:
    """csv/, json/, txt/ directories must exist."""
    required_dirs = ["csv", "json", "txt"]
    all_ok = True
    for d in required_dirs:
        dir_path = test_dir / d
        if dir_path.is_dir():
            print(f"[PASS] Directory '{d}/' exists")
        else:
            print(f"[FAIL] Directory '{d}/' not found")
            all_ok = False
    return all_ok


# ============================================================
# Check 2: Files moved with correct names
# ============================================================
def verify_files_moved_correctly(test_dir: Path) -> bool:
    """Each file must appear in the correct subdir with normalized name."""
    all_ok = True
    for original, (subdir, normalized) in EXPECTED_MOVES.items():
        target = test_dir / subdir / normalized
        if target.is_file():
            print(f"[PASS] '{subdir}/{normalized}' exists (from '{original}')")
        else:
            print(f"[FAIL] '{subdir}/{normalized}' not found (expected from '{original}')")
            all_ok = False
    return all_ok


# ============================================================
# Check 3: Empty/corrupted files deleted
# ============================================================
def verify_empty_files_deleted(test_dir: Path) -> bool:
    """
    empty_file.csv and blank.txt should be effectively removed.
    
    Acceptable outcomes (MCP filesystem server may not have delete_file):
    1. File truly deleted (not found anywhere)
    2. File content emptied (0 bytes) and NOT moved to any typed subdirectory
    3. File moved to a trash/deleted directory (not in root or typed subdirs)
    """
    all_ok = True
    for fname in SHOULD_DELETE:
        root_path = test_dir / fname
        
        # Check if file exists in typed subdirectories (always wrong)
        base = fname.lower().replace(" ", "_")
        found_in_subdir = False
        for subdir in ["csv", "json", "txt"]:
            subdir_path = test_dir / subdir
            if not subdir_path.exists():
                continue
            for f in subdir_path.iterdir():
                if f.name == fname or f.name == base:
                    print(f"[FAIL] '{fname}' should have been deleted but found as '{subdir}/{f.name}'")
                    found_in_subdir = True
                    break
            if found_in_subdir:
                break
        
        if found_in_subdir:
            all_ok = False
            continue
        
        # If file still in root, check if it was effectively emptied (acceptable workaround)
        if root_path.exists():
            content = root_path.read_text(encoding="utf-8").strip()
            if len(content) == 0:
                print(f"[PASS] '{fname}' effectively deleted (content emptied to 0 bytes)")
            else:
                print(f"[FAIL] '{fname}' still exists in root with content ({len(content)} chars)")
                all_ok = False
        else:
            print(f"[PASS] '{fname}' correctly deleted")
    
    return all_ok


# ============================================================
# Check 4: File contents not modified
# ============================================================
def verify_file_contents_intact(test_dir: Path) -> bool:
    """Spot-check that file contents were not modified during move."""
    all_ok = True

    # Check csv/sales_report.csv starts with expected header
    sales = test_dir / "csv" / "sales_report.csv"
    if sales.is_file():
        content = sales.read_text(encoding="utf-8")
        if content.startswith("date,product,amount,region"):
            print("[PASS] csv/sales_report.csv content intact")
        else:
            print("[FAIL] csv/sales_report.csv content was modified")
            all_ok = False
    else:
        print("[FAIL] csv/sales_report.csv not found for content check")
        all_ok = False

    # Check json/api_response.json contains expected key
    api = test_dir / "json" / "api_response.json"
    if api.is_file():
        content = api.read_text(encoding="utf-8")
        if '"status"' in content and "200" in content:
            print("[PASS] json/api_response.json content intact")
        else:
            print("[FAIL] json/api_response.json content was modified")
            all_ok = False
    else:
        print("[FAIL] json/api_response.json not found for content check")
        all_ok = False

    # Check txt/notes.txt contains expected content
    notes = test_dir / "txt" / "notes.txt"
    if notes.is_file():
        content = notes.read_text(encoding="utf-8")
        if "meeting" in content.lower() or "api documentation" in content.lower():
            print("[PASS] txt/notes.txt content intact")
        else:
            print("[FAIL] txt/notes.txt content was modified")
            all_ok = False
    else:
        print("[FAIL] txt/notes.txt not found for content check")
        all_ok = False

    return all_ok


# ============================================================
# Check 5: Non-target files not affected
# ============================================================
def verify_non_target_files(test_dir: Path) -> bool:
    """README.md should remain in root, not moved or deleted."""
    all_ok = True
    for fname in PRESERVED_FILES:
        fpath = test_dir / fname
        if fpath.is_file():
            print(f"[PASS] '{fname}' remains in root (non-target preserved)")
        else:
            print(f"[FAIL] '{fname}' missing from root (should not have been moved/deleted)")
            all_ok = False
    return all_ok


# ============================================================
# Check 6: Root directory cleaned
# ============================================================
def verify_root_cleaned(test_dir: Path) -> bool:
    """No .csv/.json/.txt files with real content should remain in root."""
    target_exts = {".csv", ".json", ".txt"}
    all_ok = True

    for item in test_dir.iterdir():
        if item.is_file() and item.suffix.lower() in target_exts:
            # Allow emptied files to remain (workaround for no delete_file tool)
            content = item.read_text(encoding="utf-8").strip()
            if len(content) == 0:
                continue  # Acceptable: file was emptied as deletion workaround
            print(f"[FAIL] '{item.name}' still in root with content (should have been moved or deleted)")
            all_ok = False

    if all_ok:
        print("[PASS] Root directory cleaned of .csv/.json/.txt files")
    return all_ok


# ============================================================
# Check 7: inventory.md correct
# ============================================================
def verify_inventory_file(test_dir: Path) -> bool:
    """inventory.md must exist with correct format, sections, and counts."""
    inv_path = test_dir / "inventory.md"
    if not inv_path.is_file():
        print("[FAIL] inventory.md not found in root directory")
        return False

    content = inv_path.read_text(encoding="utf-8")
    all_ok = True

    # Header
    if "# File Inventory" in content:
        print("[PASS] inventory.md has header")
    else:
        print("[FAIL] inventory.md missing '# File Inventory' header")
        all_ok = False

    # Sections
    for section in ["## csv", "## json", "## txt"]:
        if section in content.lower() or section in content:
            print(f"[PASS] inventory.md has '{section}' section")
        else:
            print(f"[FAIL] inventory.md missing '{section}' section")
            all_ok = False

    # Total line — 9 organized, 2 deleted
    if "Total:" in content or "total:" in content.lower():
        if "9" in content and "2" in content:
            print("[PASS] inventory.md total counts correct (9 organized, 2 deleted)")
        else:
            print("[FAIL] inventory.md total counts incorrect (expected 9 organized, 2 deleted)")
            all_ok = False
    else:
        print("[FAIL] inventory.md missing 'Total:' line")
        all_ok = False

    # Spot-check some file names
    spot_checks = ["sales_report.csv", "api_response.json", "notes.txt"]
    for name in spot_checks:
        if name in content:
            print(f"[PASS] inventory.md lists '{name}'")
        else:
            print(f"[FAIL] inventory.md missing '{name}'")
            all_ok = False

    # Check KB format — at least one entry should have "KB"
    if "KB" in content or "kb" in content.lower():
        print("[PASS] inventory.md includes file sizes in KB")
    else:
        print("[FAIL] inventory.md missing file sizes (expected 'X.X KB' format)")
        all_ok = False

    return all_ok


# ============================================================
# Main
# ============================================================
def main():
    """Main verification function."""
    try:
        test_dir = get_test_directory()
        print(f"[INFO] Verifying File Cleanup and Archive in: {test_dir}")
        print()

        checks = [
            ("Subdirectories exist",       verify_subdirectories_exist),
            ("Files moved correctly",       verify_files_moved_correctly),
            ("Empty files deleted",         verify_empty_files_deleted),
            ("File contents intact",        verify_file_contents_intact),
            ("Non-target files preserved",  verify_non_target_files),
            ("Root directory cleaned",      verify_root_cleaned),
            ("Inventory file correct",      verify_inventory_file),
        ]

        all_passed = True
        for check_name, check_func in checks:
            print(f"[CHECK] {check_name}...")
            if not check_func(test_dir):
                all_passed = False
            print()

        # Final result
        print("=" * 50)
        if all_passed:
            print("[SUCCESS] All verification checks passed!")
            sys.exit(0)
        else:
            print("[FAIL] Some verification checks failed!")
            sys.exit(1)

    except Exception as e:
        print(f"[FAIL] Verification failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
