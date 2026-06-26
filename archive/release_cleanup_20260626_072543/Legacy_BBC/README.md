# BBC - Bitter Brain Context

BBC is a local AI coding safety layer for large codebases. It scans the real source tree, builds a sealed project context, and gives detected AI coding tools concise rules so they work from verified facts instead of guessing.

The result is simple: fewer repeated discovery tokens, fewer hallucinated APIs, and a quieter workflow that stays out of the target project's Git history.

## What BBC Solves

AI coding assistants often waste tokens because they start without a reliable project map. They may re-read the same files, miss stale context, overlook dependency impact, or invent functions/classes that do not exist.

BBC reduces that risk by recording:

- files, symbols, imports, hashes, and dependency relationships
- freshness and symbol consistency
- task-focused context packs
- detected AI tool rule/config surfaces
- generated-code hallucination checks
- reuse-first rules so AI tools check verified existing symbols and dependencies before adding new code

BBC does not replace tests, review, or CI. It gives the AI a smaller verified operating field before it writes code.

## Measured Results

Real stress test on a cleaned legal MCP codebase:

- Files scanned: `60`
- Symbols extracted: `1,139`
- Normal source context: `165,641` tokens
- BBC sealed context: `15,455` tokens
- Tokens avoided: `150,186`
- Reduction: `90.7%`
- Verification verdict: `SEALED_STABLE`

Second full repository scan:

- Normal source context: `171,117` tokens
- BBC sealed context: `9,202` tokens
- Tokens avoided: `161,915`
- Reduction: `94.6%`

Hallucination guard test:

- Deliberately fake AI output referenced non-existing project APIs/classes.
- BBC returned `HALLUCINATION_DETECTED`.
- Match ratio: `1/6`.
- Unknown symbols were listed before the code could be trusted.

Repeatable benchmark notes live in [`benchmarks/`](benchmarks/).

## Privacy and Security

BBC is local-first.

- It does not ask for passwords, API keys, secrets, or personal data.
- It does not upload source code to a BBC server.
- It writes generated context locally under `.bbc/`.
- It updates `.gitignore` so BBC context and injected rule files do not accidentally get committed.
- `bbc publish-check` checks for BBC traces and personal path markers before publishing.
- `bbc purge` can remove BBC-generated traces from a target project.

Important: your AI IDE or assistant may have its own cloud behavior. BBC does not control those vendors. BBC's job is to reduce and verify the project context that those tools receive.

## Coverage

BBC is not tied to one IDE, one editor, or one AI assistant.

Detected AI coding surfaces may include Cursor, VS Code/GitHub Copilot, Windsurf, Continue, Cline, Roo/Kilo, JetBrains AI surfaces, Zed, Theia, Trae, Antigravity-style rule files, and other rule/config based tools.

BBC is designed for multi-language codebases. It scans common source, config, and documentation formats including Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, SQL, Markdown, JSON, YAML, and TOML. Deep symbol/dependency support is strongest where a structured parser is available; Python currently has the deepest dependency analysis.

If no active integration is detected, BBC still creates the sealed `.bbc/` context and does not mass-create IDE folders.

## Current Status

BBC v8.6 release hardening:

- Test suite: `32 passed`
- GitHub Actions CI: Windows, Linux, macOS; Python 3.10, 3.11, 3.12
- `bbc analyze`: project scan and token metrics
- `bbc verify`: syntax, freshness, symbol mismatch, stability verdict
- `bbc check`: generated-code hallucination guard
- `bbc impact`: dependency impact radius
- `bbc pack` / `bbc compile`: packed and task-focused context
- `bbc doctor`: environment, IDE signal, context, Git hygiene check
- `bbc publish-check`: no-trace publish safety check
- `bbc clean`: `.bbc/` runtime log/cache retention
- `bbc serve`: REST API health endpoint
- `bbc init`: one-shot analyze, inject, and doctor without starting a watch loop
- `bbc self-test`: local installation health check on a temporary project
- `bbc benchmark`: token reduction and context readiness report
- `bbc integrations`: detected AI coding integration support matrix
- `bbc preview`: dry-run of what BBC init will write and skip
- `bbc readiness`: combined doctor, benchmark, publish, security, and rule-health report
- `bbc security-check`: publish blockers, personal paths, and obvious secret marker scan
- `bbc rule-health`: injected rule invariant check
- `bbc mode`: records speed, quality, or balanced context mode metadata
- Adapter invariant tests: generated agent surfaces preserve evidence-only, no-hallucination, and reuse-first rules

## Installation

Requirements:

- Python 3.10+ recommended
- Git
- Permission to write inside the target project

Recommended setup:

```bash
git clone https://github.com/Anubis44197/BBC_MASTER_BBCMath.git BBC
cd BBC
pip install -r requirements.txt
python bbc.py start /path/to/your/project
```

Windows from a project folder:

```bat
git clone https://github.com/Anubis44197/BBC_MASTER_BBCMath.git BBC
BBC\setup.bat
```

Windows PowerShell:

```powershell
git clone https://github.com/Anubis44197/BBC_MASTER_BBCMath.git BBC
powershell -ExecutionPolicy Bypass -File BBC\setup.ps1
```

Linux/macOS:

```bash
git clone https://github.com/Anubis44197/BBC_MASTER_BBCMath.git BBC
bash BBC/setup.sh
```

## Commands

```bash
python bbc.py start <project>                   # Analyze, inject detected rules, start BBC
python bbc.py init <project>                    # One-shot setup without daemon/watch
python bbc.py analyze <project>                 # Build .bbc/bbc_context.json
python bbc.py verify <project>                  # Verify syntax, freshness, symbols
python bbc.py inject <project>                  # Inject rules into detected AI tools
python bbc.py check generated.py --path <project>
python bbc.py impact path/to/file.py --path <project>
python bbc.py pack --path <project> --json
python bbc.py compile --task bugfix --file path/to/file.py --path <project>
python bbc.py doctor <project>
python bbc.py self-test
python bbc.py benchmark <project>
python bbc.py integrations <project>
python bbc.py preview <project>
python bbc.py readiness <project>
python bbc.py security-check <project>
python bbc.py rule-health <project>
python bbc.py mode quality --path <project>
python bbc.py publish-check <project>
python bbc.py clean <project> --older-than-days 14
python bbc.py audit <project>
python bbc.py purge <project> --force
python bbc.py serve --port 3333
```

## How It Works

1. Scan the project and extract structural facts.
2. Seal context under `.bbc/bbc_context.json`.
3. Detect active AI coding tools from environment, process, extension, and existing-rule signals.
4. Inject concise BBC rules only into detected surfaces.
5. Verify freshness, symbol consistency, and generated code before trusting AI output.

BBC is designed to be quiet after setup. Advanced commands are available for audit, CI, and release safety, but normal use should not require repeated manual steps.

## Development

Run tests:

```bash
python -m pytest tests -q
```

If Windows temp permissions block pytest:

```bash
python -m pytest tests -q -p no:cacheprovider --basetemp .pytest-tmp
```

Before publishing:

```bash
python bbc.py publish-check .
git status --short
```

Do not commit generated target-project folders such as `.bbc/`, injected IDE rule files, or pytest temp folders.

## License

MIT
