# BBC Benchmarks

BBC benchmarks are proof-oriented checks for the product claims in the main README.
They are intentionally local-first: no source code is uploaded to a BBC service, and
the target project can be removed with `bbc purge` after a field run.

## What to Measure

1. Token reduction
   - Run `python bbc.py analyze <project>`.
   - Compare normal source context tokens with BBC sealed context tokens.
   - Record files scanned, symbols extracted, tokens avoided, and reduction percent.

2. Hallucination guard
   - Create or collect AI output that references symbols not present in the sealed context.
   - Run `python bbc.py check generated.py --path <project>`.
   - Expected result: unknown symbols are listed and unsafe output is marked before it is trusted.

3. Adapter invariants
   - Run the unit tests that cover agent adapter outputs.
   - Expected result: every generated agent surface keeps evidence-only, no-hallucination, and reuse-first rules.

4. Publish hygiene
   - Run `python bbc.py publish-check <project>`.
   - Expected result: BBC runtime traces, injected rule files, and local personal path markers are blocked before publish.

## Current Evidence Snapshot

These numbers are from local field tests and are mirrored in the README:

| Scenario | Normal tokens | BBC tokens | Tokens avoided | Reduction |
| --- | ---: | ---: | ---: | ---: |
| Legal MCP stress project | 165,641 | 15,455 | 150,186 | 90.7% |
| BBC repository scan | 171,117 | 9,202 | 161,915 | 94.6% |

Hallucination guard field check:

| Input | Result | Match ratio |
| --- | --- | ---: |
| Fake AI output with non-existing APIs/classes | `HALLUCINATION_DETECTED` | 1/6 |

## Repeatable Local Commands

```bash
python bbc.py analyze <project>
python bbc.py verify <project>
python bbc.py inject <project>
python bbc.py benchmark <project>
python bbc.py readiness <project>
python bbc.py check generated.py --path <project>
python bbc.py publish-check <project>
python -m pytest tests -q
```

For Windows temp permission issues:

```bash
python -m pytest tests -q -p no:cacheprovider --basetemp .pytest-tmp
```

## Notes

- BBC measures context reduction and verification safety, not "fewer lines of code".
- Field projects should not be committed into this repository.
- Do not publish `.bbc/`, injected IDE rule files, raw private project paths, or generated temporary test folders.
