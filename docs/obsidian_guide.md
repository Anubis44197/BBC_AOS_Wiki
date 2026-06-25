# Obsidian Integration Guide

BBC-AOS connects codebase design states to Obsidian knowledge vaults. This allows developers to link code structures, conceptual designs, and agentic trace logs directly into markdown notes.

## 1. Configuration
Set your local Obsidian vault directory path using the CLI:
```bash
bbc config set obsidian.vault_path "/path/to/your/obsidian/vault"
```

## 2. Note Promotion Rules
Notes created by agents or developers are promoted to semantic layers based on tags in note frontmatter:
* Notes containing `#promotion-ready` or `#core-spec` are automatically indexed.
* Promoted code designs are exported as clean markdown containing frontmatter tags (e.g. `is_promoted: true`, `origin: agent`).

## 3. Note Synchronization
Run notes synchronization manually:
```bash
bbc sync-obsidian
```
This maps backlinks, builds timelines, and updates concept links inside the Obsidian vault.
