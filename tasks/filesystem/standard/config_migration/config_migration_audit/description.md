Please use FileSystem tools to finish the following task:

### Task Description

You are a DevOps engineer migrating a legacy project's configuration from INI format to YAML. The project has 8 INI configuration files in the `configs/` directory, each managing different aspects of the system (database, server, cache, auth, logging, monitoring, notifications, and a legacy API). The migration must follow the rules specified in `migration_spec.md`.

Key challenges:
- Some INI sections are marked as **deprecated** (with a `; DEPRECATED` comment) and must NOT be migrated to YAML — they should be logged separately
- One entire file (`legacy_api.ini`) is fully deprecated
- Values must preserve their **correct types** in YAML (integers, booleans, floats remain unquoted; strings with special characters must be quoted)
- **Comma-separated values** should be converted to YAML lists
- **Cross-file conflicts** exist: the same key name appears in multiple files with different values — these must be detected and reported
- All original files must be **backed up** before processing

### Task Objectives

1. **Read the migration specification** from `migration_spec.md` to understand all rules

2. **Create output directories**: `yaml/`, `backup/`

3. **Back up original files**: Copy each `.ini` file to `backup/` with a timestamp suffix (e.g., `database.ini` → `backup/database_20260211.ini`)

4. **Convert each INI file to YAML format**:
   - Each `[section]` becomes a top-level YAML key
   - Key-value pairs become nested under their section
   - **Type preservation**:
     - Integers (e.g., `port = 5432`) → `port: 5432` (no quotes)
     - Booleans (e.g., `enabled = true`) → `enabled: true` (no quotes)
     - Floats (e.g., `error_rate_warning = 0.01`) → `error_rate_warning: 0.01`
     - Comma-separated lists (e.g., `hosts = a,b,c`) → YAML list format
     - Strings with special characters → quoted
   - **Skip deprecated sections** entirely — do not include them in YAML output
   - For the fully deprecated `legacy_api.ini`, create a YAML file with only a comment noting it's deprecated

5. **Generate `deprecated.log`** listing all deprecated sections:
   ```
   [database.ini] replication: Old replication settings, use new cluster config instead
   [server.ini] static: Old static file serving, moved to CDN
   ...
   ```

6. **Detect cross-file key conflicts** and generate `conflicts.md`:
   - Scan all non-deprecated sections across all files
   - Find keys with the same name but different values in different files
   - Report format:
   ```
   # Cross-File Key Conflicts

   ## Key: connection_timeout
   | File | Section | Value |
   |------|---------|-------|
   | database.ini | connection | 30 |
   | cache.ini | redis | 10 |
   ...
   ```

7. **Generate `changelog.md`** summarizing the migration:
   ```
   # Configuration Migration Changelog

   ## database.ini → yaml/database.yaml
   - Sections migrated: N
   - Sections deprecated: N
   - Keys migrated: N
   ...
   ```

### Constraints

- Do not modify original INI files — only read them
- YAML files must be syntactically valid
- Deprecated sections must NOT appear in any YAML output file
- All INI comments starting with `;` should be converted to `#` in YAML (preserve header comments only)
- Type detection must be accurate — `"5432"` as a string in YAML would be incorrect for a port number
- Backup filenames must include a date suffix

### Expected Outcome

After task completion:
- `yaml/` directory with 8 YAML files (7 with content, 1 nearly empty for legacy_api)
- `backup/` directory with 8 backed-up INI files with timestamp suffixes
- `deprecated.log` listing all 8 deprecated sections from 6 files
- `conflicts.md` documenting cross-file key name conflicts
- `changelog.md` with per-file migration summary
- No deprecated section content in any YAML file
- Proper YAML formatting with type preservation

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
