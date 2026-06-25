# Tasks - Repository Layout Restructuring & Productization

- `[x]` Create new directory structure (`src/`, `tests/`, `docs/`, `examples/`, `tools/`, `archive/`)
- `[x]` Adopt `src/` layout (move `bbc_aos/` to `src/bbc_aos/` and clean up)
- `[x]` Convert validation scripts to pytest-compatible tests under `tests/`
- `[x]` Create helper/utility scripts under `tools/`
- `[x]` Create root governance files (`CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `MANIFEST.in`, `pyproject.toml`, `Dockerfile`, `LICENSE`)
- `[x]` Organize documentation under `docs/`
- `[x]` Relocate legacy, specs, reports, old validation scripts, and historical docs to `archive/`
- `[x]` Update and run `tools/sync_phase13a.py` to synchronize workspace to Desktop copy
- `[x]` Verify clean structure and confirm zero-regression
- `[x]` Modify `pyproject.toml`
- `[x]` Implement Click CLI in `src/bbc_aos/main.py`
- `[x]` Create GitHub Actions workflows (`.github/workflows/ci.yml` and `.github/workflows/certification.yml`)
- `[x]` Verify pytests
- `[x]` Build and verify wheel packaging locally
