# BBC User Guide

## What BBC Creates

In the target project, BBC keeps operational files under:

```text
.bbc/
```

Depending on detected AI tools, BBC may also create one rule/config file such as:

```text
.github/copilot-instructions.md
.cursorrules
.clinerules
.windsurf/bbc_rules.md
.antigravity/rules.md
```

BBC does not intentionally create every supported integration. It writes only to detected active surfaces.

## Recommended Workflow

```bash
python bbc.py analyze <project>
python bbc.py verify <project>
python bbc.py inject <project>
python bbc.py status <project>
```

For live monitoring:

```bash
python bbc.py start <project> --background
python bbc.py stop <project>
```

## Command Reference

| Command | Purpose |
|---|---|
| `analyze <project>` | Build sealed context |
| `analyze <project> --incremental` | Reuse cached segments and re-analyze changes |
| `verify <project>` | Check syntax, freshness, symbols, and stability |
| `inject <project>` | Write rules for detected AI tools |
| `check <file> --path <project>` | Check generated code against sealed context |
| `impact <file> --path <project>` | Show direct and indirect dependency impact |
| `pack --path <project> --json` | Emit compact machine-readable context |
| `compile --task bugfix --file <file> --path <project>` | Build task-focused context |
| `telemetry <project>` | Show project-scoped command telemetry |
| `remember <topic> <content> --path <project>` | Save project memory |
| `recall <query> --path <project>` | Search project memory |
| `audit <project>` | Show BBC traces in a target project |
| `purge <project> --force` | Remove BBC traces from a target project |
| `serve --port 3333` | Start the local REST API |

## IDE Detection

BBC combines several signals:

- explicit environment variables
- active process names and command lines
- known extension folders
- existing rule files inside the target project

If no IDE or extension is detected, BBC still keeps `.bbc/bbc_context.json` available for manual use.

## Token Metrics

BBC uses `tiktoken` when installed. If unavailable, it uses deterministic fallback estimates.

Real IDE usage calibration is conservative:

- Cursor usage can be read from `state.vscdb` when accessible.
- Unsupported or inaccessible IDE stores return fallback status.
- BBC does not use synthetic token data for calibration.

## Publishing a Target Project

Before pushing a target project to GitHub:

```bash
python bbc.py audit <project>
python bbc.py purge <project> --force
git status --short
```

BBC-generated traces are also covered by `.gitignore` patterns.

## Troubleshooting

### Python dependency errors

Run:

```bash
pip install -r requirements.txt
```

### Context is stale

Run:

```bash
python bbc.py analyze <project>
python bbc.py verify <project>
```

### AI tool did not receive rules

Run:

```bash
python bbc.py inject <project>
python bbc.py audit <project>
```

Then restart the IDE if necessary.

### Pytest temp permission issue on Windows

Use repo-local temp:

```bash
python -m pytest tests -q -p no:cacheprovider --basetemp .pytest-tmp
```
