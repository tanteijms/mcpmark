#!/usr/bin/env python3
"""
Verification script for PyPI Dependency Chain Investigation task.

Checks the model's <answer> output against expected values in label.txt.
10 fields across 3 PyPI pages + 1 cross-page synthesis question.
"""

import sys
import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


# =============================================================================
# MCP MESSAGE PARSING
# =============================================================================


def get_model_response() -> Optional[str]:
    messages_path = os.getenv("MCP_MESSAGES")
    print(f"| MCP_MESSAGES: {messages_path}")
    if not messages_path:
        print("| Warning: MCP_MESSAGES environment variable not set", file=sys.stderr)
        return None

    try:
        with open(messages_path, "r") as f:
            messages = json.load(f)

        for message in reversed(messages):
            if message.get("role") == "assistant":
                content = message.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") in [
                            "text",
                            "output_text",
                        ]:
                            text = item.get("text", "")
                            if "<answer>" in text:
                                return text
                    all_text = " ".join(
                        item.get("text", "")
                        if isinstance(item, dict)
                        else str(item)
                        for item in content
                    )
                    if "<answer>" in all_text:
                        return all_text
                elif isinstance(content, str):
                    if "<answer>" in content:
                        return content

        for message in reversed(messages):
            if message.get("role") == "assistant":
                content = message.get("content", [])
                if isinstance(content, list):
                    full_text = " ".join(
                        item.get("text", "")
                        if isinstance(item, dict)
                        else str(item)
                        for item in content
                    )
                elif isinstance(content, str):
                    full_text = content
                else:
                    continue
                if "<answer>" in full_text:
                    return full_text

        print(
            "| Warning: No assistant message with <answer> tag found", file=sys.stderr
        )
        return None
    except Exception as e:
        print(f"| Error reading messages file: {str(e)}", file=sys.stderr)
        return None


# =============================================================================
# ANSWER PARSING
# =============================================================================


def parse_answer_format(text: str) -> Optional[Dict[str, str]]:
    if not text:
        return None

    match = re.search(r"<answer>(.*?)</answer>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None

    answer_content = match.group(1).strip()
    result = {}

    for line in answer_content.split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        key, value = line.split("|", 1)
        result[key.strip()] = value.strip()

    return result


def load_expected_answer(label_path: Path) -> Optional[Dict[str, str]]:
    try:
        with open(label_path, "r") as f:
            lines = f.read().strip().split("\n")

        expected = {}
        for line in lines:
            line = line.strip()
            if not line or "|" not in line:
                continue
            key, value = line.split("|", 1)
            expected[key.strip()] = value.strip()

        return expected
    except Exception as e:
        print(f"| Error reading label file: {str(e)}", file=sys.stderr)
        return None


# =============================================================================
# FIELD COMPARISON FUNCTIONS
# =============================================================================


def compare_exact(model_val: str, expected_val: str, field: str) -> Tuple[bool, str]:
    if model_val.strip() == expected_val.strip():
        return True, f"✓ {field}: exact match"
    return False, f"✗ {field}: expected '{expected_val}', got '{model_val}'"


def compare_exact_ci(model_val: str, expected_val: str, field: str) -> Tuple[bool, str]:
    if model_val.strip().lower() == expected_val.strip().lower():
        return True, f"✓ {field}: match (case-insensitive)"
    return False, f"✗ {field}: expected '{expected_val}', got '{model_val}'"


def compare_contains(
    model_val: str, expected_val: str, field: str
) -> Tuple[bool, str]:
    if expected_val.lower() in model_val.lower():
        return True, f"✓ {field}: contains expected content"
    if model_val.lower() in expected_val.lower():
        return True, f"✓ {field}: contained in expected content"
    return False, f"✗ {field}: expected to contain '{expected_val}', got '{model_val}'"


def compare_number(
    model_val: str, expected_val: str, field: str
) -> Tuple[bool, str]:
    """Compare numeric values, allowing ±1 tolerance for dep counts."""
    try:
        m = int(model_val.strip())
        e = int(expected_val.strip())
        if m == e:
            return True, f"✓ {field}: exact count match ({m})"
        if abs(m - e) == 1:
            return True, f"✓ {field}: count within tolerance ({m} vs expected {e})"
        return False, f"✗ {field}: expected {e}, got {m}"
    except ValueError:
        return False, f"✗ {field}: could not parse as number: '{model_val}'"


def compare_dep_list(
    model_val: str, expected_val: str, field: str
) -> Tuple[bool, str]:
    """
    Compare dependency lists with flexible matching.
    - Case-insensitive
    - Allow minor naming differences (e.g., importlib_metadata vs importlib-metadata)
    - Require at least N-1 of expected dependencies
    """
    def normalize(name: str) -> str:
        return name.strip().lower().replace("_", "-").replace(" ", "")

    model_deps = set(normalize(d) for d in model_val.split(",") if d.strip())
    expected_deps = set(normalize(d) for d in expected_val.split(",") if d.strip())

    found = model_deps & expected_deps
    missing = expected_deps - model_deps
    extra = model_deps - expected_deps

    min_required = max(len(expected_deps) - 1, 1)

    details = []
    details.append(f"  Found {len(found)}/{len(expected_deps)} expected dependencies")
    if missing:
        details.append(f"  Missing: {', '.join(sorted(missing))}")
    if extra:
        details.append(f"  Extra: {', '.join(sorted(extra))}")

    if len(found) >= min_required:
        return (
            True,
            f"✓ {field}: {len(found)}/{len(expected_deps)} dependencies found\n"
            + "\n".join(details),
        )
    else:
        return (
            False,
            f"✗ {field}: only {len(found)}/{len(expected_deps)} dependencies found (need {min_required})\n"
            + "\n".join(details),
        )


def compare_python_version(
    model_val: str, expected_val: str, field: str
) -> Tuple[bool, str]:
    """Compare Python version requirements with normalization."""
    m = model_val.strip().replace(" ", "")
    e = expected_val.strip().replace(" ", "")
    if m == e:
        return True, f"✓ {field}: exact match"
    if e in m or m in e:
        return True, f"✓ {field}: partial match"
    return False, f"✗ {field}: expected '{expected_val}', got '{model_val}'"


# =============================================================================
# MAIN VERIFICATION
# =============================================================================

FIELD_COMPARATORS = {
    "FlaskDepCount": compare_number,
    "FlaskDeps": compare_dep_list,
    "FlaskPython": compare_python_version,
    "WerkzeugSummary": compare_contains,
    "WerkzeugPython": compare_python_version,
    "WerkzeugDeps": compare_dep_list,
    "Jinja2Summary": compare_contains,
    "Jinja2Python": compare_python_version,
    "Jinja2Deps": compare_dep_list,
    "SharedTransitiveDep": compare_exact_ci,
}

REQUIRED_FIELDS = ["FlaskDeps", "SharedTransitiveDep"]

# All fields must pass for the task to pass (MCPMark convention)


def verify() -> bool:
    print("| " + "=" * 60)
    print("| Verifying PyPI Dependency Chain Investigation Task")
    print("| " + "=" * 60)

    label_path = Path(__file__).parent / "label.txt"
    expected = load_expected_answer(label_path)
    if not expected:
        print("| Error: Could not load expected answer from label.txt", file=sys.stderr)
        return False

    print(f"| Loaded {len(expected)} expected fields from label.txt")

    model_response = get_model_response()
    if not model_response:
        print("| Error: No model response found", file=sys.stderr)
        return False

    print(f"| Model response length: {len(model_response)} characters")

    model_answer = parse_answer_format(model_response)
    if not model_answer:
        print("| Error: Could not parse <answer> format from response", file=sys.stderr)
        print(
            f"| Response preview: {model_response[:300]}...",
            file=sys.stderr,
        )
        return False

    print(f"| Parsed {len(model_answer)} fields from model answer")
    print("| " + "-" * 60)

    for field in REQUIRED_FIELDS:
        if field not in model_answer:
            print(
                f"| FAIL: Required field '{field}' missing from model answer",
                file=sys.stderr,
            )
            return False

    total_fields = len(expected)
    passed_fields = 0
    results = []

    for field, expected_val in expected.items():
        model_val = model_answer.get(field, "")

        if not model_val:
            result_msg = f"✗ {field}: field not found in model answer"
            results.append((False, result_msg))
            continue

        comparator = FIELD_COMPARATORS.get(field, compare_exact)
        passed, msg = comparator(model_val, expected_val, field)

        results.append((passed, msg))
        if passed:
            passed_fields += 1

    print("| " + "-" * 60)
    print("| Field-by-field comparison:")
    for passed, msg in results:
        for line in msg.split("\n"):
            print(f"| {line}")
    print("| " + "-" * 60)

    all_passed = all(p for p, _ in results)
    print(f"| Score: {passed_fields}/{total_fields}")

    if all_passed:
        print("| " + "=" * 60)
        print("| ✓ TASK PASSED")
        print("| " + "=" * 60)
        return True
    else:
        print("| " + "=" * 60)
        print("| ✗ TASK FAILED")
        print("| " + "=" * 60)
        return False


def main():
    try:
        success = verify()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"| Verification error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
