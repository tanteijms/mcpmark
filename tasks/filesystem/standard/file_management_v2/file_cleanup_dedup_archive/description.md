Please use FileSystem tools to finish the following task:

### Task Description

You are a data engineer responsible for cleaning up a shared team workspace. Multiple team members have dumped files across nested subdirectories over several months. The workspace contains CSV, JSON, and TXT files scattered across `inbox/`, `downloads/` (with date-based subdirectories), `shared/`, and the root directory. The files suffer from multiple issues:

- **Naming inconsistency**: Mixed case, spaces in filenames, uppercase extensions
- **Duplicate files**: Some files exist in multiple locations with different names but identical content
- **Corrupted data**: Some JSON files contain syntax errors and cannot be parsed
- **Empty files**: Some files contain only whitespace or are completely empty
- **Draft documents**: Some files are preliminary drafts (identifiable by "DRAFT" in the filename)

Your task is to systematically clean, validate, deduplicate, and organize this workspace.

### Task Objectives

1. **Recursively scan all subdirectories** to discover every file in the workspace

2. **Create the target directory structure**:
   - `organized/csv/`, `organized/json/`, `organized/txt/` — for valid, unique data files
   - `drafts/` — for draft documents
   - `quarantine/` — for malformed/corrupted files
   - `trash/` — for empty or whitespace-only files

3. **Apply processing rules in this priority order** for each `.csv`, `.json`, `.txt` file:

   **Rule A — Empty/Whitespace Check**: If the file is empty or contains only whitespace characters, move it to `trash/`.

   **Rule B — Draft Detection**: If the filename contains "DRAFT" (case-insensitive), move it to `drafts/`. Normalize the filename (lowercase, spaces to underscores).

   **Rule C — JSON Validation**: For `.json` files, check if the content is valid JSON. If it cannot be parsed (missing brackets, trailing commas, syntax errors), move it to `quarantine/` with an `.invalid` extension appended (e.g., `broken.json` → `quarantine/broken.json.invalid`).

   **Rule D — Duplicate Detection**: Compare file contents to detect duplicates. If two or more files have identical content, keep only one copy (the first one encountered alphabetically by full path) and do not organize the rest.

   **Rule E — Organize**: Move the remaining valid, unique files into `organized/{type}/` based on extension. Normalize filenames: all lowercase, spaces replaced with underscores.

4. **Preserve non-target files**: Files with non-target extensions (e.g., `.md`) must remain untouched in their original locations.

5. **Generate three report files** in the workspace root:

   **`inventory.md`** — List all organized files grouped by type, with file sizes:
   ```
   # File Inventory

   ## csv
   - filename.csv (X.X KB)
   ...

   ## json
   - filename.json (X.X KB)
   ...

   ## txt
   - filename.txt (X.X KB)
   ...

   Total: N files organized
   ```
   File sizes calculated as `bytes / 1024`, rounded to 1 decimal place. Files listed alphabetically within each section.

   **`duplicates_report.md`** — Document all detected duplicate groups:
   ```
   # Duplicates Report

   ## Duplicate Group 1
   - Original: <kept file path>
   - Duplicate: <removed file path>
   ...
   ```

   **`audit_summary.md`** — Provide processing statistics:
   ```
   # Audit Summary

   - Total files scanned: N
   - Files organized: N
   - Duplicates removed: N
   - Files quarantined: N
   - Draft files separated: N
   - Empty files discarded: N
   ```

### Constraints

- Do not modify the content of any data file — only move, rename, and organize
- Only process files with `.csv`, `.json`, or `.txt` extensions (case-insensitive)
- All non-target files (`.md` etc.) must remain untouched in their original locations
- Reports must accurately reflect the final state of the workspace
- When deduplicating, keep the copy whose full original path comes first alphabetically

### Expected Outcome

After task completion, the workspace should contain:
- `organized/csv/` with exactly the unique, valid CSV files (properly renamed)
- `organized/json/` with exactly the valid, parseable JSON files (properly renamed)
- `organized/txt/` with exactly the non-draft, non-empty TXT files (properly renamed)
- `drafts/` with draft documents separated from the main organization
- `quarantine/` with malformed JSON files clearly marked
- `trash/` with empty/whitespace files moved out of the workspace
- Three report files (`inventory.md`, `duplicates_report.md`, `audit_summary.md`) accurately documenting the entire cleanup process
- All `.md` files in their original locations, untouched

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
