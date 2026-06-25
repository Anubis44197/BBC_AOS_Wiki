# Phase 13A - Obsidian User Guide

This guide describes how to connect and sync your BBC-AOS codebase with your Obsidian knowledge vault.

---

## 1. Overview

BBC-AOS features native integration with Obsidian. This allows developer-designed architectures, API contracts, and sync proposals to be managed as markdown notes directly inside your knowledge vault.

---

## 2. Vault Configuration

Configure your Obsidian vault path using the `bbc` CLI tool:
```bash
bbc config set obsidian.vault_path "/Users/developer/Documents/Obsidian/BBC_Math_Vault"
```
This registers the vault target path in the platform configuration database.

---

## 3. Core Commands

### Sync Notes
To sync codebase symbols, call dependencies, and active designs to your vault:
```bash
bbc sync-obsidian
```
This generates structured markdown files under the `bbc_code/` subdirectory inside your vault.

### Query Knowledge
To query note similarity:
```bash
bbc obsidian search "Gauss-Jordan matrix inverse"
```

---

## 4. Semantic Note Promotion

Markdown notes inside Obsidian can be promoted to production code if they comply with frontmatter guidelines:

1. **Create a Note**: Design your class or function inside a markdown note (e.g. `jwt_auth.md`).
2. **Configure Frontmatter**:
   ```yaml
   ---
   bbc_status: draft
   target_file: bbc_aos/api/auth.py
   target_symbol: JWTAuth
   dependencies:
     - bbc_aos/core/config.py
   ---
   ```
3. **Request Promotion**: Update `bbc_status` to `proposal`.
4. **Compile & Sync**: Run `bbc sync-obsidian`. The platform automatically intercepts the note proposal, parses the code block, and routes the request to the `AgentOrchestrator` chain for validation, human approval, and sandbox commit.
