# Vault Path Validation Report

Phase: C13 Real User Pilot Hardening
Date: 2026-06-27
Mode: No commits, no pushes

## Fix

Implemented a single canonical resolver:

```text
bbc_aos.wiki.paths.resolve_workspace_vault()
```

Canonical vault path:

```text
workspace_root/BBC_KNOWLEDGE
```

The resolver rejects:

- paths outside the workspace
- non-canonical nested vault paths inside the workspace
- default writes to user home, source checkout, site-packages, or temp install directories

## Updated Call Sites

- `bbc init`
- `bbc obsidian connect`
- `bbc wiki status`
- `bbc wiki search`
- `WikiCompiler`
- `bbc ask` vault artifact writer
- loop state export

## Smoke Result

Workspace:

```text
C:\tmp\bbc_c13_smoke
```

Resolved vault:

```text
C:\tmp\bbc_c13_smoke\BBC_KNOWLEDGE
```

Result: PASS.

The generated `.bbc/config.json` used the workspace-local vault path.

## Tests

Added coverage:

- canonical workspace vault resolution
- outside-workspace rejection
- non-canonical inside-workspace rejection
- `WikiCompiler` project creation under `workspace_root/BBC_KNOWLEDGE`

Verdict: PASS.
