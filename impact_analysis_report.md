# Impact Analysis Report

Date: 2026-06-27

## Change Impact Matrix

BBC now produces grouped file impact data for every context resolution:

- PRIMARY
- DIRECT
- INDIRECT
- TRANSITIVE

The matrix is persisted in ContextAgent audit details and packed context.

## Scoring

BBC now calculates:

- `blast_radius_score`: 0-100
- `blast_radius_class`: SMALL, MEDIUM, LARGE, MASSIVE
- `affected_file_count`

Classification rules:

- LARGE: more than 20 files or score >= 70
- MASSIVE: more than 50 files or score >= 90

## Validation

The mevzuat MCP validation scenarios produced 35-36 affected files and MASSIVE classification.

## Hallucination Check

Displayed affected files were checked against the target repository. Hallucinated files: 0.

Verdict: READY FOR EXTREME PILOT RETEST
