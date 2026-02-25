# PyPI Dependency Chain Investigation

Use Playwright MCP tools to investigate Flask 3.0.0's dependency tree by navigating to **multiple PyPI package pages** and synthesizing cross-page information.

## Task

You are conducting a dependency audit for Flask 3.0.0. You need to visit three different PyPI package pages, extract metadata from each, and identify shared transitive dependencies.

### Step 1: Investigate Flask 3.0.0

Navigate to `https://pypi.org/project/Flask/3.0.0/` and extract:
- The total **count** of required dependencies (do NOT count optional/extras dependencies, but DO count dependencies with Python version conditions — they are still required)
- The complete **list** of required dependency package names
- The **Python version** requirement

### Step 2: Investigate Werkzeug 3.0.0

Navigate to `https://pypi.org/project/Werkzeug/3.0.0/` and extract:
- The one-line **summary** description
- The **Python version** requirement
- ALL **required** dependency package names (not extras)

### Step 3: Investigate Jinja2 3.1.2

Navigate to `https://pypi.org/project/Jinja2/3.1.2/` and extract:
- The one-line **summary** description
- The **Python version** requirement
- ALL **required** dependency package names (not extras)

### Step 4: Cross-Page Synthesis

Based on your findings from all three pages, determine:
- The **shared transitive dependency**: which package appears as a required dependency of BOTH Werkzeug 3.0.0 AND Jinja2 3.1.2?

## Output Format

You MUST output your findings using EXACTLY this format (no extra text, no explanations):

```
<answer>
FlaskDepCount|number
FlaskDeps|dep1,dep2,dep3,...
FlaskPython|version
WerkzeugSummary|text
WerkzeugPython|version
WerkzeugDeps|dep1,dep2,...
Jinja2Summary|text
Jinja2Python|version
Jinja2Deps|dep1,dep2,...
SharedTransitiveDep|package_name
</answer>
```

## Example Output (for hypothetical packages)

```
<answer>
FlaskDepCount|4
FlaskDeps|alpha,beta,gamma,delta
FlaskPython|>=3.9
WerkzeugSummary|A web toolkit library.
WerkzeugPython|>=3.8
WerkzeugDeps|libfoo,libbar
Jinja2Summary|A template engine.
Jinja2Python|>=3.7
Jinja2Deps|libfoo,libqux
SharedTransitiveDep|libfoo
</answer>
```

## Important Notes

- You MUST visit all three specific version pages: Flask 3.0.0, Werkzeug 3.0.0, Jinja2 3.1.2
- Only count/list **required** dependencies — ignore optional dependencies marked as "extra"
- Dependencies with Python version conditions (e.g., `; python_version < "3.10"`) are still **required** — include them in your count and list
- Dependency lists must be comma-separated, in **alphabetical order**, no spaces after commas
- The final output must contain ONLY the `<answer>` block — no additional text or explanations
- Wait for each page to fully load before extracting data

Note: Based on your understanding, solve the task all at once by yourself, don't ask for my opinions on anything.
