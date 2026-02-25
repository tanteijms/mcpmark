# Configuration Migration Specification

## Objective

Migrate all INI configuration files in `configs/` to YAML format following the rules below.

## Rules

### 1. File Conversion
- Convert each `.ini` file to a corresponding `.yaml` file in a `yaml/` directory
- File naming: `database.ini` → `yaml/database.yaml`

### 2. Type Preservation
During conversion, preserve value types:
- Integers: `port = 5432` → `port: 5432`
- Booleans: `enabled = true` → `enabled: true`
- Floats: `error_rate_warning = 0.01` → `error_rate_warning: 0.01`
- Strings: all other values remain as strings (quote if they contain special characters like `#`, `$`, `!`, `&`, `{`, `}`, `[`, `]`)
- Comma-separated lists: `hosts = a,b,c` → convert to YAML list format

### 3. Section Nesting
INI sections become top-level YAML keys:
```
[connection]
host = localhost
port = 5432
```
becomes:
```yaml
connection:
  host: localhost
  port: 5432
```

### 4. Deprecated Sections
- Sections marked with `; DEPRECATED` comment (on the line immediately before the section header, or as part of the file header comments) should NOT be included in the YAML output
- Instead, log each deprecated section to `deprecated.log` with format:
  `[filename] section_name: <reason if available from comments>`
- If an entire file is deprecated (header comment says so), create a YAML file with only a comment noting it's deprecated and log ALL sections

### 5. Comments
- INI comments (`;`) should be converted to YAML comments (`#`)
- Only preserve file header/documentation comments, not inline comments after values

### 6. Backup
- Copy each original `.ini` file to `backup/` directory before processing
- Rename with date suffix: `database.ini` → `backup/database_20260211.ini`

### 7. Cross-File Conflict Detection
- Scan all files for keys with the same name in different files (across all non-deprecated sections)
- If the same key name appears in multiple files with DIFFERENT values, record in `conflicts.md`
- Format: markdown table with Key name, File, Section, and Value columns

### 8. Changelog
- Generate `changelog.md` documenting every file processed:
  - Original filename → new filename
  - Sections migrated (count)
  - Sections deprecated (count)
  - Keys migrated (count)

## Output Structure
```
yaml/                    # Converted YAML files
backup/                  # Original INI backups with date suffix
deprecated.log           # All deprecated sections listed
changelog.md             # Migration summary per file
conflicts.md             # Cross-file key conflicts
```
