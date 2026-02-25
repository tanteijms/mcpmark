Please use GitHub tools to finish the following task:

### Task Description

You are a new engineering manager taking over a repository. Your first task is to conduct a structured Repository Health Audit: set up project management infrastructure (labels), create issues for identified problems, submit a documentation remediation PR, and produce a summary audit issue that ties everything together.

### Task Objectives

#### Step 1: Create Standardized Labels

Create the following 8 labels with **exact names** and descriptions:

| Label | Description | Color |
|-------|-------------|-------|
| `audit:critical` | Critical audit finding requiring immediate action | `#d73a4a` |
| `audit:high` | High priority audit finding | `#e99695` |
| `audit:medium` | Medium priority audit finding | `#fbca04` |
| `audit:low` | Low priority finding for future improvement | `#0e8a16` |
| `type:bug` | Something isn't working correctly | `#d73a4a` |
| `type:docs` | Documentation improvements needed | `#0075ca` |
| `type:security` | Security-related issue | `#7057ff` |
| `type:maintenance` | Maintenance and infrastructure tasks | `#cfd3d7` |

#### Step 2: Create Audit Issues

Create exactly **5 audit issues** with the following specifications:

**Issue 1**: "Missing CONTRIBUTING.md — no contributor guidelines"
- Labels: `type:docs`, `audit:high`
- Body must contain: description of why contributing guidelines are important, suggested sections (Code of Conduct, How to Submit, Style Guide)

**Issue 2**: "No branch protection documentation or security policy"
- Labels: `type:security`, `audit:critical`
- Body must contain: recommendation for SECURITY.md, mention of responsible disclosure

**Issue 3**: "README lacks installation and setup instructions"
- Labels: `type:docs`, `audit:medium`
- Body must contain: specific sections that should be added (Prerequisites, Installation, Quick Start)

**Issue 4**: "No CI/CD pipeline configured"
- Labels: `type:maintenance`, `audit:high`
- Body must contain: recommendation for GitHub Actions, mention of automated testing

**Issue 5**: "Missing LICENSE file — legal risk"
- Labels: `type:docs`, `audit:critical`
- Body must contain: recommendation for MIT License, mention of legal compliance

#### Step 3: Create Remediation Branch and Files

1. Create a branch named `audit/health-check-remediation` from the default branch

2. Create the following files on that branch:

   **`CONTRIBUTING.md`** — Must contain:
   - A "How to Contribute" section
   - A "Code of Conduct" reference
   - Contribution workflow steps (fork, branch, PR)
   - At least 200 characters of content

   **`LICENSE`** — Must contain:
   - MIT License text
   - Year 2026
   - The repository owner's name or organization

   **`SECURITY.md`** — Must contain:
   - "Security Policy" heading
   - "Reporting a Vulnerability" section
   - Contact email or instructions for responsible disclosure

#### Step 4: Create Pull Request

Create a pull request from `audit/health-check-remediation` to the default branch:
- Title must contain "Audit" and "Remediation" (case-insensitive)
- Body must explain what files were added and why

#### Step 5: Create Audit Summary Issue

Create a 6th issue titled "[Audit Summary] Repository Health Check Results":
- Labels: `audit:high`, `type:maintenance`
- Body must contain:
  - A table or list summarizing all 5 audit findings (issue number, title, severity)
  - References to ALL 5 audit issues using `#N` syntax
  - A reference to the remediation PR using `#N` syntax
  - An "Overall Assessment" section
  - A "Next Steps" section

#### Step 6: Add Comments to Issues

Add a comment to each of the 5 audit issues (not the summary) with a remediation plan:
- Each comment must be at least 50 characters long
- Each comment must mention either "priority", "timeline", or "remediation"

### Constraints

- All label names must be exact (case-sensitive)
- Issue titles must match the specifications exactly
- The PR must target the default branch (usually `main` or `master`)
- Do not modify existing repository files — only add new ones

### Expected Outcome

After task completion:
- 8 labels created with correct names and descriptions
- 6 issues total (5 audit + 1 summary), each with correct labels
- 1 branch with 3 new files (CONTRIBUTING.md, LICENSE, SECURITY.md)
- 1 pull request with audit remediation content
- Summary issue cross-referencing all findings and the PR
- 5 comments on audit issues with remediation plans

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
