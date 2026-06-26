# CLI Validation Report

Result: BLOCKED

Validated command surface:
- `bbc --help`: PASS
- `bbc init`: PASS
- `bbc doctor`: PASS
- `bbc index`: PASS
- `bbc ask --shadow`: PASS
- `bbc benchmark`: PASS
- `bbc failures`: PASS
- `bbc wiki status`: PASS
- `bbc wiki search`: PASS
- `bbc loop init`: PASS
- `bbc loop audit`: PASS
- `bbc loop status`: PASS
- `bbc loop budget`: PASS
- `bbc loop patterns`: PASS
- `bbc loop metrics`: PASS
- `bbc obsidian connect`: PASS
- invalid command handling: PASS
- missing argument handling: PASS
- malformed loop mode handling: PASS as nonzero

Blocking observation:
- `bbc ask "review current project"` is interactive and exits nonzero in unattended validation because approval prompt aborts without stdin confirmation. This is safe behavior, but automation needs a noninteractive dry-run or explicit approval fixture.
