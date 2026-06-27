# Approval Visibility Report

Date: 2026-06-27

## Implemented

`bbc ask --shadow` now displays approval-grade impact data even when no patch is applied:

- Risk
- Blast Radius file count
- Score
- Class
- Files that would change
- Change impact matrix
- Telemetry

## Example Validation Output

Architecture Refactor:

- Risk: HIGH
- Blast Radius: 35 files
- Score: 94
- Class: MASSIVE
- PRIMARY: 12 files
- DIRECT: 3 files
- INDIRECT: 2 files
- TRANSITIVE: 18 files

## Fix

Previously, review/simulation work often printed an empty affected-file list because only `modified_files`, `added_files`, and `removed_files` were displayed. Shadow output now falls back to ContextAgent `selected_files`.

Verdict: READY FOR EXTREME PILOT RETEST
