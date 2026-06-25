# BBC-AOS Developer Behavior Model

| Task Type | Frequency | Risk Level | BBC Action |
| --- | --- | --- | --- |
| Bug fix | Very high | MEDIUM | try/except + logger |
| Code review | Very high | LOW | analysis report |
| New feature | High | MEDIUM-HIGH | function stub + import |
| Refactor | Medium | MEDIUM | type annotation + docstring |
| Test | Very high | LOW-MEDIUM | pytest test stub |
| Documentation | Low | LOW | docstring |

BBC-AOS uses this model to choose how aggressively it should patch, estimate risk, and ask for the right approval level.
