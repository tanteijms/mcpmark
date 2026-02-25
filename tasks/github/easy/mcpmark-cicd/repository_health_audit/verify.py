#!/usr/bin/env python3
"""
Verification for Repository Health Audit & Remediation v3 (GitHub MCP)
9 checks covering labels, issues, PR, files, cross-references, comments.
(v3: milestone removed, PR issue-reference requirement removed)
"""

import sys
import os
import re

try:
    from github import Github
except ImportError:
    print("PyGithub not installed, trying requests fallback")
    Github = None

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(".mcp_env")
except ImportError:
    pass


def get_github_client():
    """Get GitHub API client."""
    token = os.environ.get("MCP_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("MCP_GITHUB_TOKEN or GITHUB_TOKEN required")
    return token


def get_repo_info():
    """Get repository owner and name from GITHUB_EVAL_ORG + hardcoded repo name."""
    repo_full = os.environ.get("GITHUB_REPOSITORY")
    if repo_full:
        parts = repo_full.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
    owner = os.environ.get("GITHUB_EVAL_ORG")
    if owner:
        return owner, "mcpmark-cicd"
    raise ValueError("GITHUB_REPOSITORY or GITHUB_EVAL_ORG env var required")


def gh_api(endpoint, token):
    """Make a GitHub API request."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com{endpoint}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def gh_api_list(endpoint, token):
    """Make paginated GitHub API request."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    results = []
    page = 1
    while True:
        url = f"https://api.github.com{endpoint}{'&' if '?' in endpoint else '?'}page={page}&per_page=100"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        page += 1
        if len(data) < 100:
            break
    return results


# ============================================================
# Step 1: Labels (8 required)
# ============================================================
def verify_labels(token, owner, repo) -> bool:
    labels = gh_api_list(f"/repos/{owner}/{repo}/labels", token)
    label_names = {l["name"] for l in labels}

    required = [
        "audit:critical", "audit:high", "audit:medium", "audit:low",
        "type:bug", "type:docs", "type:security", "type:maintenance"
    ]

    all_ok = True
    found = 0
    for r in required:
        if r in label_names:
            found += 1
        else:
            print(f"    [FAIL] Label '{r}' not found")
            all_ok = False

    if all_ok:
        print(f"  [PASS] All 8 labels found")
    else:
        print(f"  Found {found}/8 required labels")
    return all_ok


# ============================================================
# Step 2: Issue count (6 total: 5 audit + 1 summary)
# ============================================================
def verify_issue_count(token, owner, repo) -> bool:
    issues = gh_api_list(f"/repos/{owner}/{repo}/issues?state=open&per_page=100", token)
    real_issues = [i for i in issues if "pull_request" not in i]

    if len(real_issues) >= 6:
        print(f"  [PASS] At least 6 issues found ({len(real_issues)} total)")
        return True
    else:
        print(f"  [FAIL] Expected at least 6 issues, found {len(real_issues)}")
        return False


# ============================================================
# Step 3: Issue labels correct
# ============================================================
def verify_issue_labels(token, owner, repo) -> bool:
    issues = gh_api_list(f"/repos/{owner}/{repo}/issues?state=open&per_page=100", token)
    real_issues = [i for i in issues if "pull_request" not in i]

    audit_labels_found = set()
    for issue in real_issues:
        labels = {l["name"] for l in issue.get("labels", [])}
        audit_labels_found.update(labels)

    required_label_types = ["audit:critical", "audit:high", "type:docs", "type:security", "type:maintenance"]
    found_count = sum(1 for l in required_label_types if l in audit_labels_found)

    if found_count >= 4:
        print(f"  [PASS] Issues use {found_count}/5 required label types")
        return True
    else:
        print(f"  [FAIL] Issues only use {found_count}/5 required label types")
        return False


# ============================================================
# Step 4: Branch exists
# ============================================================
def verify_branch(token, owner, repo) -> bool:
    try:
        gh_api(f"/repos/{owner}/{repo}/branches/audit/health-check-remediation", token)
        print(f"  [PASS] Branch 'audit/health-check-remediation' exists")
        return True
    except Exception:
        try:
            gh_api(f"/repos/{owner}/{repo}/branches/audit%2Fhealth-check-remediation", token)
            print(f"  [PASS] Branch 'audit/health-check-remediation' exists")
            return True
        except Exception:
            print(f"  [FAIL] Branch 'audit/health-check-remediation' not found")
            return False


# ============================================================
# Step 5: PR exists (title check only, no issue-reference requirement)
# ============================================================
def verify_pr(token, owner, repo) -> bool:
    prs = gh_api_list(f"/repos/{owner}/{repo}/pulls?state=all&per_page=100", token)

    for pr in prs:
        title = pr.get("title", "").lower()
        if "audit" in title and "remediation" in title:
            print(f"  [PASS] PR found: '{pr['title']}'")
            return True

    print(f"  [FAIL] No PR found with 'Audit' and 'Remediation' in title")
    return False


# ============================================================
# Step 6: Files exist on branch
# ============================================================
def verify_files_on_branch(token, owner, repo) -> bool:
    branch = "audit/health-check-remediation"
    required_files = ["CONTRIBUTING.md", "LICENSE", "SECURITY.md"]
    all_ok = True

    for filename in required_files:
        try:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}?ref={branch}"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                print(f"    [PASS] {filename} exists on branch")
            else:
                print(f"    [FAIL] {filename} not found on branch")
                all_ok = False
        except Exception:
            print(f"    [FAIL] Error checking {filename}")
            all_ok = False

    return all_ok


# ============================================================
# Step 7: Summary issue cross-references
# ============================================================
def verify_summary_issue(token, owner, repo) -> bool:
    issues = gh_api_list(f"/repos/{owner}/{repo}/issues?state=open&per_page=100", token)
    real_issues = [i for i in issues if "pull_request" not in i]

    summary = None
    for issue in real_issues:
        title = issue.get("title", "").lower()
        if "summary" in title or "audit summary" in title:
            summary = issue
            break

    if not summary:
        print("  [FAIL] Summary issue not found (title should contain 'Summary')")
        return False

    body = summary.get("body", "") or ""
    issue_refs = re.findall(r'#(\d+)', body)
    unique_refs = set(issue_refs)

    all_ok = True

    if len(unique_refs) >= 5:
        print(f"  [PASS] Summary references {len(unique_refs)} unique issues/PRs")
    else:
        print(f"  [FAIL] Summary only references {len(unique_refs)} unique items (expected >= 5)")
        all_ok = False

    body_lower = body.lower()
    if "assessment" in body_lower or "overall" in body_lower:
        print("  [PASS] Summary contains assessment section")
    else:
        print("  [FAIL] Summary missing 'Overall Assessment' section")
        all_ok = False

    if "next steps" in body_lower or "next step" in body_lower:
        print("  [PASS] Summary contains next steps")
    else:
        print("  [FAIL] Summary missing 'Next Steps' section")
        all_ok = False

    return all_ok


# ============================================================
# Step 8: Comments on audit issues
# ============================================================
def verify_comments(token, owner, repo) -> bool:
    issues = gh_api_list(f"/repos/{owner}/{repo}/issues?state=open&per_page=100", token)
    real_issues = [i for i in issues if "pull_request" not in i]

    audit_issues = [i for i in real_issues
                    if "summary" not in i.get("title", "").lower()]

    issues_with_comments = 0
    for issue in audit_issues[:5]:
        comments = gh_api_list(
            f"/repos/{owner}/{repo}/issues/{issue['number']}/comments",
            get_github_client()
        )
        if len(comments) >= 1:
            for c in comments:
                body = (c.get("body", "") or "").lower()
                if len(body) >= 50 and any(kw in body for kw in ["priority", "timeline", "remediation"]):
                    issues_with_comments += 1
                    break

    if issues_with_comments >= 4:
        print(f"  [PASS] {issues_with_comments} audit issues have quality comments")
        return True
    elif issues_with_comments >= 3:
        print(f"  [WARN] Only {issues_with_comments} issues have quality comments")
        return True
    else:
        print(f"  [FAIL] Only {issues_with_comments} issues have quality comments (expected >= 4)")
        return False


# ============================================================
# Step 9: LICENSE file content check
# ============================================================
def verify_license_content(token, owner, repo) -> bool:
    branch = "audit/health-check-remediation"
    try:
        import base64
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/LICENSE?ref={branch}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print("  [FAIL] LICENSE file not accessible")
            return False

        data = resp.json()
        content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")

        all_ok = True
        if "mit" in content.lower() or "permission is hereby granted" in content.lower():
            print("  [PASS] LICENSE contains MIT license text")
        else:
            print("  [FAIL] LICENSE does not contain MIT license text")
            all_ok = False

        if "2026" in content:
            print("  [PASS] LICENSE contains year 2026")
        else:
            print("  [FAIL] LICENSE missing year 2026")
            all_ok = False

        return all_ok
    except Exception as e:
        print(f"  [FAIL] Error checking LICENSE: {e}")
        return False


# ============================================================
# Main
# ============================================================
def main():
    token = get_github_client()
    owner, repo = get_repo_info()

    print(f"Verifying repository: {owner}/{repo}")

    verification_steps = [
        ("Step 1: Labels (8 required)", lambda: verify_labels(token, owner, repo)),
        ("Step 2: Issue Count (>= 6)", lambda: verify_issue_count(token, owner, repo)),
        ("Step 3: Issue Labels Correct", lambda: verify_issue_labels(token, owner, repo)),
        ("Step 4: Remediation Branch Exists", lambda: verify_branch(token, owner, repo)),
        ("Step 5: PR Exists", lambda: verify_pr(token, owner, repo)),
        ("Step 6: Files on Branch", lambda: verify_files_on_branch(token, owner, repo)),
        ("Step 7: Summary Issue Cross-References", lambda: verify_summary_issue(token, owner, repo)),
        ("Step 8: Comments on Issues", lambda: verify_comments(token, owner, repo)),
        ("Step 9: LICENSE Content", lambda: verify_license_content(token, owner, repo)),
    ]

    all_passed = True
    results = []

    for step_name, verify_func in verification_steps:
        print(f"\n{'='*55}")
        print(f"  {step_name}")
        print(f"{'='*55}")
        try:
            passed = verify_func()
            results.append((step_name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append((step_name, False))
            all_passed = False

    print(f"\n{'='*55}")
    print("  VERIFICATION SUMMARY")
    print(f"{'='*55}")
    for step_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {step_name}")

    passed_count = sum(1 for _, p in results if p)
    print(f"\n  Result: {passed_count}/{len(results)} steps passed")

    if all_passed:
        print("\n  OVERALL: ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("\n  OVERALL: SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
