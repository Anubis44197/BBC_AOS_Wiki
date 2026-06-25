# Obsidian Integration Guide

BBC-AOS connects codebase design states to Obsidian knowledge vaults. This allows developers to link code structures, conceptual designs, and agentic trace logs directly into markdown notes.

## 1. Connection Management
Connect, disconnect, or check the status of your Obsidian vault using the CLI.

### Connect to a Vault
Set your local Obsidian vault directory path to link it with BBC-AOS:
```bash
bbc obsidian connect "/path/to/your/obsidian/vault"
```
This writes the vault path configuration to `.bbc/config.json`.

### Check Connection Status
Verify the current active connection and configuration:
```bash
bbc obsidian status
```
* **CONNECTED**: Displays the absolute path of the connected vault.
* **DISCONNECTED**: Indicates that no vault is connected (standalone mode).

### Disconnect Vault
Remove the connected Obsidian vault:
```bash
bbc obsidian disconnect
```

---

## 2. Note Promotion Rules
Notes created by agents or developers are promoted to semantic layers based on tags in note frontmatter:
* Notes containing `#promotion-ready` or `#core-spec` are automatically indexed.
* Promoted code designs are exported as clean markdown containing frontmatter tags (e.g. `is_promoted: true`, `origin: agent`).

---

## 3. Proposal and Approvals Workflow
When running `bbc ask`, note proposals are automatically written to `BBC_Wiki/Approvals/` and copied to the connected Obsidian vault.

To manage proposals:
* **List pending proposals**: `bbc wiki pending`
* **Approve proposal**: `bbc wiki approve <note_id>`
  * Moves the note from `Approvals/` to the target category folder (e.g. `Architecture/`, `Decisions/`, `Executions/`).
  * Changes status from `PROPOSED` to `APPROVED` inside the markdown frontmatter.
  * Registers the note to the semantic memory layer of BBC-AOS.
  * Synchronizes the approved note to the connected Obsidian vault.
* **Reject proposal**: `bbc wiki reject <note_id>`
  * Moves the note to `Approvals/rejected/`.
  * Sets status to `REJECTED` in frontmatter.
  * Removes the pending proposal from the connected Obsidian vault.

---

## 4. Note Synchronization
Run notes synchronization manually:
```bash
bbc sync-obsidian
```
This maps backlinks, builds timelines, and updates concept links inside the Obsidian vault.

