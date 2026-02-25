Please use FileSystem tools to finish the following task:

### Task Description

You are a data analyst working with a messy downloads directory. Various data files have accumulated without any organization — CSV, JSON, and TXT files are mixed together in a flat directory. Some files have inconsistent naming (mixed case, spaces in names), and a few files are empty or corrupted (contain only whitespace). Your task is to clean up and organize this directory.

### Task Objectives

1. **Create typed subdirectories** — `csv/`, `json/`, `txt/` under the working directory
2. **Move each data file** into the corresponding subdirectory based on its extension (case-insensitive: `.JSON` and `.json` both go to `json/`)
3. **Rename files** during the move to follow a consistent naming convention:
   - All lowercase
   - Replace spaces with underscores
   - Example: `Sales Report.csv` → `csv/sales_report.csv`
4. **Delete empty or corrupted files** — any file whose content is empty or contains only whitespace should be removed entirely (not moved to any subdirectory)
5. **Create an inventory file** named `inventory.md` in the working directory root with the following exact format:

```
# File Inventory

## csv
- filename.csv (X.X KB)

## json
- filename.json (X.X KB)

## txt
- filename.txt (X.X KB)

Total: X files organized, Y files deleted
```

File sizes should be calculated as `bytes / 1024`, rounded to 1 decimal place. Files within each section should be listed in alphabetical order.

### Constraints

- Do not modify the content of any data file — only move, rename, and organize
- Only process files with `.csv`, `.json`, or `.txt` extensions (case-insensitive); ignore all other file types (e.g., `.md` files should remain untouched)
- The inventory must accurately reflect the final state after cleanup
- Empty subdirectories should still be created even if no files of that type exist

### Expected Outcome

After task completion, the working directory should contain:
- Three typed subdirectories (`csv/`, `json/`, `txt/`) each containing properly renamed data files
- All files renamed to lowercase with underscores replacing spaces
- No empty or whitespace-only files remaining anywhere in the directory
- Non-target files (such as `.md` files) remaining untouched in their original location
- An `inventory.md` file at the root accurately listing all organized files with sizes, grouped by type, sorted alphabetically, with a summary total line

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
