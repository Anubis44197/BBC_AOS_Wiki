# GitHub Release Checklist

## Required Before Public Release

- [x] README updated
- [x] LICENSE present
- [x] CHANGELOG present
- [x] SECURITY present
- [x] CONTRIBUTING present
- [x] CODE_OF_CONDUCT present
- [x] Ruff passes
- [x] Mypy passes
- [x] Pytest passes
- [x] Wheel build passes
- [x] Clean install passes
- [x] Shadow mode checksum validation passes
- [x] Security validation blocks all malicious scenarios
- [ ] Repository root cleanup approved and completed
- [ ] GitHub CI rerun green
- [ ] GitHub certification workflow green
- [ ] Docker build verified - blocked locally because Docker Desktop Linux engine is not running
- [ ] Real repository benchmark executed with non-placeholder metrics

## Release Decision

Status: NOT READY

Reason:
- Cleanup and external validation items remain open.
- Docker CLI is installed, but the Docker Desktop Linux engine is unavailable locally.
