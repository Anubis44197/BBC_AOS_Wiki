# Phase 13A - Obsidian Configuration Reference

This reference details Obsidian vault configuration schemas, folder hierarchies, and metadata keys.

---

## 1. Directory Structure

Inside the designated Obsidian vault, the following structure is created and maintained by the platform:

```
Obsidian_Vault/
├── .obsidian/                 # Obsidian settings
├── bbc_code/                  # Auto-generated code semantic documentation
│   ├── classes/               # Compiled class documentation markdown notes
│   ├── functions/             # Compiled function documentation markdown notes
│   └── modules/               # Module dependency maps
├── bbc_proposals/             # Developer-created change proposals
│   └── draft_auth_jwt.md      # Example proposal note
└── bbc_invariants/            # System guardrail policies and contract notes
```

---

## 2. Frontmatter Configuration Schema

All proposal notes under `bbc_proposals/` must comply with this frontmatter schema:

| Metadata Key | Data Type | Valid Values | Description |
| :--- | :--- | :--- | :--- |
| **`bbc_status`** | String | `draft`, `proposal`, `approved`, `rejected` | Transition state of the proposal. |
| **`target_file`** | String | Valid relative file path | File targeted for code generation. |
| **`target_symbol`** | String | Valid python identifier | Name of class/function to extract. |
| **`dependencies`** | List of Strings | Valid file paths | Scope files required for compilation. |
| **`risk_override`** | String | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Optional manual risk rating. |

---

## 3. Configuration Parameters

Register settings in the main SQLite configuration database:
* `obsidian.vault_path`: Absolute path to vault.
* `obsidian.sync_on_startup`: Boolean (defaults to `false`).
* `obsidian.default_risk_routing`: String (defaults to `MEDIUM`).
