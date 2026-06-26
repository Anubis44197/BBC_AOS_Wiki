# Repository Cleanup Report

Result: BLOCKED

Completed:
- Ruff scope restored for production release validation.
- `scratch`, `archive`, `Legacy_BBC`, root duplicate `bbc_aos`, build/cache directories are excluded from lint where appropriate.
- `.gitignore` restored for local BBC knowledge vault directories.

Blocked:
- Broad root reorganization was not executed because it would move/delete major directories:
  - `Legacy_BBC`
  - root duplicate `bbc_aos`
  - `Reports`
  - `Specs`
  - `scratch`
  - historical root markdown inventories

Required explicit cleanup approval:
- Move legacy/prod-external material under `archive/`.
- Delete transient caches: `__pycache__`, `.pytest_cache`, `.mypy_cache`, `build`.
- Keep release wheel artifacts only when intentionally publishing.

Current release impact:
- Source validation passes.
- Public repository root is not yet clean according to the requested final root layout.
