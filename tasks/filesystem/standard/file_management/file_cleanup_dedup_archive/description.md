Please use FileSystem tools to finish the following task:

### Task Description

You are a data engineer responsible for cleaning up a large shared team workspace. Multiple team members have dumped files across deeply nested subdirectories over several months. The workspace contains CSV, JSON, and TXT files scattered across `inbox/`, `downloads/` (with quarterly date subdirectories), `shared/`, `archive/`, and the root directory. The files suffer from multiple issues:

- **Naming inconsistency**: Mixed case, spaces in filenames, uppercase extensions
- **Duplicate files**: Some files exist in multiple locations with different names but **byte-for-byte identical content**
- **Near-duplicate files**: Some files have very similar names/content but **differ slightly** (e.g., an updated version with additional data) — these are NOT duplicates and must both be kept
- **Corrupted data**: Some JSON files contain syntax errors (missing brackets, trailing commas, single quotes instead of double quotes) and cannot be parsed
- **Empty files**: Some files contain only whitespace or are completely empty
- **Draft documents**: Some files are preliminary drafts (identifiable by "DRAFT" in the filename, case-insensitive)
- **Hidden files**: Files starting with `.` (e.g., `.gitignore`) that should be preserved
- **Priority conflicts**: Some files may match multiple rules (e.g., a draft that is also empty) — rules must be applied in strict priority order

Your task is to systematically clean, validate, deduplicate, and organize this workspace.

### Task Objectives

1. **Recursively scan all subdirectories** to discover every file in the workspace

2. **Create the target directory structure**:
   - `organized/csv/`, `organized/json/`, `organized/txt/` — for valid, unique data files
   - `drafts/` — for draft documents
   - `quarantine/` — for malformed/corrupted files
   - `trash/` — for empty or whitespace-only files

3. **Apply processing rules in STRICT priority order** for each `.csv`, `.json`, `.txt` file:

   **Rule A — Empty/Whitespace Check (HIGHEST PRIORITY)**: If the file is empty or contains only whitespace characters, move it to `trash/`. This takes precedence over ALL other rules — even if the filename contains "DRAFT", an empty file goes to trash, not drafts.

   **Rule B — Draft Detection**: If the filename contains "DRAFT" (case-insensitive) AND the file is not empty, move it to `drafts/`. Normalize the filename (lowercase, spaces to underscores).

   **Rule C — JSON Validation**: For `.json` files, verify the content is valid JSON by checking for common syntax errors (missing closing brackets, trailing commas, single quotes used instead of double quotes, etc.). If the content cannot be parsed as valid JSON, move it to `quarantine/` with an `.invalid` extension appended (e.g., `broken.json` → `quarantine/broken.json.invalid`).

   **Rule D — Duplicate Detection**: Compare file contents to detect **exact duplicates** (byte-for-byte identical content). If two or more files have identical content, keep only one copy (the first encountered alphabetically by full original path) and do not organize the duplicates. **Important**: Files with similar but not identical content (e.g., an updated version with additional rows) are NOT duplicates and must both be organized.

   **Rule E — Organize**: Move remaining valid, unique files into `organized/{type}/` based on extension. Normalize filenames: all lowercase, spaces replaced with underscores.

4. **Preserve non-target files**: Files with non-target extensions (`.md`, `.gitignore`, etc.) and hidden files (starting with `.`) must remain untouched in their original locations.

5. **Generate three report files** in the workspace root:

   **`inventory.md`** — List all organized files grouped by type, with file sizes:
   ```
   # File Inventory

   ## csv (N files)
   - filename.csv (X.X KB)
   ...
   Subtotal: X.X KB

   ## json (N files)
   - filename.json (X.X KB)
   ...
   Subtotal: X.X KB

   ## txt (N files)
   - filename.txt (X.X KB)
   ...
   Subtotal: X.X KB

   Total: N files organized, X.X KB total
   ```
   File sizes calculated as `bytes / 1024`, rounded to 1 decimal place. Files listed alphabetically within each section. Include subtotals per category and grand total.

   **`duplicates_report.md`** — Document all detected duplicate groups:
   ```
   # Duplicates Report

   ## Duplicate Group 1
   - Kept: <path of kept file>
   - Removed: <path of duplicate>
   ...

   Total: N duplicate files removed
   ```

   **`audit_summary.md`** — Provide processing statistics:
   ```
   # Audit Summary

   - Total files scanned: N
   - Files organized: N (csv: N, json: N, txt: N)
   - Duplicates removed: N
   - Files quarantined: N
   - Draft files separated: N
   - Empty files discarded: N
   - Files preserved (non-target): N
   ```
   All numbers must be internally consistent and match the actual final state.

### Constraints

- Do not modify the content of any data file — only move, rename, and organize
- Only process files with `.csv`, `.json`, or `.txt` extensions (case-insensitive)
- All non-target files (`.md`, `.gitignore`, etc.) and hidden files must remain untouched
- Rule priority is absolute: A > B > C > D > E
- Reports must be internally consistent — the numbers in audit_summary.md must match what's actually in the directories and what's listed in inventory.md
- When deduplicating, compare actual file content, not filenames — files with similar names but different content are NOT duplicates

### Expected Outcome

After task completion, the workspace should contain:
- `organized/csv/` with the unique, valid CSV files (properly renamed)
- `organized/json/` with the valid, parseable JSON files (properly renamed)
- `organized/txt/` with the non-draft, non-empty TXT files (properly renamed)
- `drafts/` with non-empty draft documents
- `quarantine/` with malformed JSON files clearly marked
- `trash/` with empty/whitespace files (including any drafts that were empty)
- Three report files with accurate, internally consistent statistics
- All `.md` files and hidden files in their original locations, untouched

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
