#!/usr/bin/env python3
"""
Verification script for Configuration Migration & Audit Task
Ground truth:
  8 INI files, 31 total sections, 8 deprecated sections across 6 files
  Deprecated: database/replication, server/static, auth/ldap, logging/elasticsearch,
              notifications/sms, legacy_api/{endpoints,mapping,compatibility}
  Cross-file conflicts: port, host, password, enabled, connection_timeout, timeout, etc.
"""

import sys
import os
import re
from pathlib import Path


def get_test_directory() -> Path:
    test_root = os.environ.get("FILESYSTEM_TEST_DIR")
    if not test_root:
        raise ValueError("FILESYSTEM_TEST_DIR environment variable is required")
    return Path(test_root)


# INI files and their deprecated sections
INI_FILES = [
    "database", "server", "cache", "auth",
    "logging", "monitoring", "notifications", "legacy_api"
]

DEPRECATED_SECTIONS = {
    "database.ini": ["replication"],
    "server.ini": ["static"],
    "auth.ini": ["ldap"],
    "logging.ini": ["elasticsearch"],
    "notifications.ini": ["sms"],
    "legacy_api.ini": ["endpoints", "mapping", "compatibility"],
}

# Keys that should NOT appear in YAML (from deprecated sections)
DEPRECATED_KEYS = {
    "replication": ["master_host", "slave_hosts", "replication_lag_threshold"],
    "static": ["root_path", "cache_max_age"],
    "ldap": ["base_dn", "bind_dn", "bind_password", "search_filter"],
    "elasticsearch": ["index_pattern", "bulk_size", "flush_interval"],
    "sms": ["account_sid", "auth_token", "from_number", "escalation_numbers"],
    "endpoints": ["base_url", "api_key"],
    "mapping": ["user_endpoint", "product_endpoint", "order_endpoint"],
    "compatibility": ["response_format", "charset"],
}

# Type check: these values should appear as numbers (not quoted) in YAML
TYPE_CHECK_NUMBERS = {
    "database.yaml": {"port": 5432, "max_connections": 20, "idle_timeout": 300},
    "server.yaml": {"port": 8080, "workers": 4, "max_age": 86400},
    "monitoring.yaml": {"cpu_warning": 70, "cpu_critical": 90, "scrape_interval": 15},
}

# Type check: these should be booleans
TYPE_CHECK_BOOLEANS = {
    "database.yaml": ["enabled"],
    "server.yaml": ["keep_alive", "enabled"],
    "cache.yaml": ["secure", "http_only"],
}


def verify_yaml_directory(test_dir: Path) -> bool:
    """yaml/ directory must exist with YAML files."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    yaml_files = [f.name for f in yaml_dir.iterdir() if f.is_file() and f.suffix in (".yaml", ".yml")]
    print(f"  Found {len(yaml_files)} YAML files: {sorted(yaml_files)}")

    if len(yaml_files) >= 7:
        print("  [PASS] At least 7 YAML files created")
        return True
    else:
        print(f"  [FAIL] Expected at least 7 YAML files, found {len(yaml_files)}")
        return False


def verify_yaml_not_ini_format(test_dir: Path) -> bool:
    """YAML files should not contain INI format markers."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    all_ok = True
    for f in yaml_dir.iterdir():
        if f.is_file() and f.suffix in (".yaml", ".yml"):
            content = f.read_text(encoding="utf-8", errors="replace")
            # Check for INI section headers [section_name]
            ini_sections = re.findall(r'^\[[\w]+\]', content, re.MULTILINE)
            if ini_sections:
                print(f"    [FAIL] {f.name} contains INI section markers: {ini_sections[:3]}")
                all_ok = False
            # Check for INI-style key=value (not key: value)
            ini_kvs = re.findall(r'^\w+\s*=\s*\S', content, re.MULTILINE)
            yaml_kvs = re.findall(r'^\s*\w+\s*:\s*', content, re.MULTILINE)
            if ini_kvs and not yaml_kvs:
                print(f"    [FAIL] {f.name} uses INI format (key=value) instead of YAML (key: value)")
                all_ok = False
            elif yaml_kvs:
                print(f"    [PASS] {f.name} uses YAML format")

    return all_ok


def verify_deprecated_sections_excluded(test_dir: Path) -> bool:
    """Deprecated section keys must NOT appear in YAML output."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    all_ok = True
    for f in yaml_dir.iterdir():
        if f.is_file() and f.suffix in (".yaml", ".yml"):
            content = f.read_text(encoding="utf-8", errors="replace").lower()
            for section, keys in DEPRECATED_KEYS.items():
                for key in keys:
                    # Check for the key as a YAML key (word: or word =)
                    if re.search(rf'^\s*{re.escape(key)}\s*:', content, re.MULTILINE):
                        # Check if it's in a comment line
                        lines = content.split('\n')
                        for line in lines:
                            stripped = line.strip()
                            if stripped.startswith('#'):
                                continue
                            if re.match(rf'\s*{re.escape(key)}\s*:', stripped):
                                print(f"    [FAIL] Deprecated key '{key}' (from [{section}]) found in {f.name}")
                                all_ok = False
                                break

    if all_ok:
        print("  [PASS] No deprecated section keys found in YAML files")
    return all_ok


def verify_legacy_api_yaml(test_dir: Path) -> bool:
    """legacy_api.yaml should be nearly empty (all sections deprecated)."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    # Find the legacy_api yaml file
    legacy_file = None
    for f in yaml_dir.iterdir():
        if f.is_file() and "legacy" in f.name.lower():
            legacy_file = f
            break

    if not legacy_file:
        print("  [FAIL] No legacy_api YAML file found")
        return False

    content = legacy_file.read_text(encoding="utf-8", errors="replace")
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    non_comment_lines = [l for l in lines if not l.startswith('#')]

    if len(non_comment_lines) <= 2:
        print(f"  [PASS] {legacy_file.name} is effectively empty ({len(non_comment_lines)} non-comment lines)")
        return True
    else:
        print(f"  [FAIL] {legacy_file.name} has {len(non_comment_lines)} non-comment lines (should be nearly empty)")
        return False


def verify_type_preservation(test_dir: Path) -> bool:
    """Check that numerical values are not quoted as strings in YAML."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    all_ok = True
    checks_passed = 0
    checks_total = 0

    for filename, expected in TYPE_CHECK_NUMBERS.items():
        yaml_file = yaml_dir / filename
        if not yaml_file.is_file():
            # Try .yml extension
            yaml_file = yaml_dir / filename.replace(".yaml", ".yml")
        if not yaml_file.is_file():
            continue

        content = yaml_file.read_text(encoding="utf-8", errors="replace")
        for key, value in expected.items():
            checks_total += 1
            # Look for key: value (unquoted number)
            pattern_good = rf'{key}\s*:\s*{value}\b'
            # Look for key: "value" or key: 'value' (quoted = bad)
            pattern_bad = rf'{key}\s*:\s*["\'].*{value}.*["\']'

            if re.search(pattern_bad, content):
                print(f"    [FAIL] {filename}: {key} is quoted (should be numeric)")
                all_ok = False
            elif re.search(pattern_good, content):
                checks_passed += 1

    if checks_total > 0:
        print(f"    [PASS] Type preservation: {checks_passed}/{checks_total} numeric values unquoted")
    return all_ok


def verify_backup_directory(test_dir: Path) -> bool:
    """backup/ should contain backed-up INI files."""
    backup_dir = test_dir / "backup"
    if not backup_dir.is_dir():
        print("  [FAIL] backup/ directory not found")
        return False

    backup_files = list(backup_dir.iterdir())
    if len(backup_files) >= 7:
        print(f"  [PASS] backup/ has {len(backup_files)} files")
        # Check for date suffix pattern
        has_date = any(re.search(r'2026', f.name) for f in backup_files if f.is_file())
        if has_date:
            print("    [PASS] Backup files have date suffix")
        else:
            print("    [WARN] Backup files may not have date suffix")
        return True
    else:
        print(f"  [FAIL] backup/ has only {len(backup_files)} files (expected 8)")
        return False


def verify_deprecated_log(test_dir: Path) -> bool:
    """deprecated.log should list all deprecated sections."""
    dep_log = test_dir / "deprecated.log"
    if not dep_log.is_file():
        # Try alternative names
        for alt in ["deprecated.txt", "deprecated.md"]:
            if (test_dir / alt).is_file():
                dep_log = test_dir / alt
                break

    if not dep_log.is_file():
        print("  [FAIL] deprecated.log not found")
        return False

    content = dep_log.read_text(encoding="utf-8").lower()

    all_ok = True
    found = 0
    total = 0

    for filename, sections in DEPRECATED_SECTIONS.items():
        for section in sections:
            total += 1
            if section in content:
                found += 1

    if found >= 6:  # At least 6 of 8 deprecated sections mentioned
        print(f"  [PASS] deprecated.log mentions {found}/{total} deprecated sections")
    elif found >= 4:
        print(f"  [WARN] deprecated.log mentions {found}/{total} deprecated sections")
    else:
        print(f"  [FAIL] deprecated.log only mentions {found}/{total} deprecated sections")
        all_ok = False

    # Legacy API should be prominently mentioned
    if "legacy" in content:
        print("    [PASS] Legacy API file mentioned")
    else:
        print("    [FAIL] Legacy API file not mentioned")
        all_ok = False

    return all_ok


def verify_changelog(test_dir: Path) -> bool:
    """changelog.md should document migration of all files."""
    changelog = test_dir / "changelog.md"
    if not changelog.is_file():
        print("  [FAIL] changelog.md not found")
        return False

    content = changelog.read_text(encoding="utf-8").lower()

    all_ok = True
    files_mentioned = 0

    for ini_name in INI_FILES:
        if ini_name in content:
            files_mentioned += 1

    if files_mentioned >= 7:
        print(f"  [PASS] changelog.md references {files_mentioned}/8 configuration files")
    elif files_mentioned >= 5:
        print(f"  [WARN] changelog.md references {files_mentioned}/8 configuration files")
    else:
        print(f"  [FAIL] changelog.md only references {files_mentioned}/8 files")
        all_ok = False

    # Should mention migration counts
    has_counts = bool(re.search(r'section', content)) and bool(re.search(r'\d+', content))
    if has_counts:
        print("    [PASS] changelog.md includes section/key counts")
    else:
        print("    [WARN] changelog.md may not include counts")

    return all_ok


def verify_conflicts_report(test_dir: Path) -> bool:
    """conflicts.md should document cross-file key conflicts."""
    conflicts = test_dir / "conflicts.md"
    if not conflicts.is_file():
        print("  [FAIL] conflicts.md not found")
        return False

    content = conflicts.read_text(encoding="utf-8").lower()

    all_ok = True

    # Key conflicts that must exist:
    # connection_timeout: database=30, cache=10
    # port: database=5432, server=8080/8443, cache=6379, logging=514, monitoring=9090, notifications=587, auth=636
    # host: database=db-primary..., cache=cache-cluster..., logging=syslog...
    # password: database=Kj#9$..., cache=R3d!s$..., notifications=Sm!tp...

    expected_conflicts = [
        ("port", True),
        ("host", True),
        ("password", False),
        ("connection_timeout", False),
        ("enabled", False),
    ]

    found_count = 0
    for key, required in expected_conflicts:
        if key in content:
            found_count += 1
            print(f"    [PASS] Conflict for '{key}' documented")
        elif required:
            print(f"    [FAIL] Conflict for '{key}' not documented")
            all_ok = False

    if found_count >= 3:
        print(f"  [PASS] {found_count} key conflicts documented")
    elif found_count >= 2:
        print(f"  [WARN] Only {found_count} key conflicts documented")
    else:
        print(f"  [FAIL] Insufficient conflict documentation ({found_count})")
        all_ok = False

    return all_ok


def verify_content_spot_check(test_dir: Path) -> bool:
    """Spot-check specific values in YAML outputs."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    all_ok = True
    checks = 0
    passed = 0

    # Check database.yaml has connection section with host
    for f in yaml_dir.iterdir():
        if f.is_file() and "database" in f.name.lower():
            content = f.read_text(encoding="utf-8", errors="replace")
            checks += 1
            if "db-primary.internal.company.com" in content:
                passed += 1
                print("    [PASS] database: connection host correct")
            else:
                print("    [FAIL] database: connection host missing")
                all_ok = False
            break

    # Check server.yaml has cors with allowed_origins
    for f in yaml_dir.iterdir():
        if f.is_file() and "server" in f.name.lower():
            content = f.read_text(encoding="utf-8", errors="replace")
            checks += 1
            if "app.company.com" in content:
                passed += 1
                print("    [PASS] server: cors allowed_origins present")
            else:
                print("    [FAIL] server: cors allowed_origins missing")
                all_ok = False
            break

    # Check monitoring.yaml has thresholds
    for f in yaml_dir.iterdir():
        if f.is_file() and "monitoring" in f.name.lower():
            content = f.read_text(encoding="utf-8", errors="replace")
            checks += 1
            if "0.01" in content or "error_rate_warning" in content:
                passed += 1
                print("    [PASS] monitoring: thresholds present")
            else:
                print("    [FAIL] monitoring: thresholds missing")
                all_ok = False
            break

    print(f"    Content spot check: {passed}/{checks}")
    return all_ok


def verify_comma_lists_converted(test_dir: Path) -> bool:
    """Comma-separated values should be converted to YAML lists."""
    yaml_dir = test_dir / "yaml"
    if not yaml_dir.is_dir():
        print("  [FAIL] yaml/ directory not found")
        return False

    all_ok = True

    # Check server.yaml: allowed_origins should be a list
    for f in yaml_dir.iterdir():
        if f.is_file() and "server" in f.name.lower():
            content = f.read_text(encoding="utf-8", errors="replace")
            # YAML list indicators: "- item" or "[item1, item2]"
            has_list = bool(re.search(r'^\s*-\s+', content, re.MULTILINE)) or \
                       bool(re.search(r'\[.*,.*\]', content))
            if has_list:
                print("    [PASS] YAML list format detected in server config")
            else:
                # Check if comma values are still in INI format
                if "GET,POST,PUT" in content:
                    print("    [FAIL] Comma-separated values not converted to YAML list")
                    all_ok = False
                else:
                    print("    [WARN] Could not verify list conversion format")
            break

    return all_ok


def main():
    test_dir = get_test_directory()

    print(f"Test directory: {test_dir}")

    verification_steps = [
        ("Step 1: YAML Directory & Files", verify_yaml_directory),
        ("Step 2: YAML Format (Not INI)", verify_yaml_not_ini_format),
        ("Step 3: Deprecated Sections Excluded", verify_deprecated_sections_excluded),
        ("Step 4: Legacy API YAML (Empty)", verify_legacy_api_yaml),
        ("Step 5: Type Preservation (Numbers)", verify_type_preservation),
        ("Step 6: Backup Directory", verify_backup_directory),
        ("Step 7: Deprecated Log", verify_deprecated_log),
        ("Step 8: Changelog", verify_changelog),
        ("Step 9: Conflicts Report", verify_conflicts_report),
        ("Step 10: Content Spot Check", verify_content_spot_check),
        ("Step 11: Comma Lists Converted", verify_comma_lists_converted),
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
