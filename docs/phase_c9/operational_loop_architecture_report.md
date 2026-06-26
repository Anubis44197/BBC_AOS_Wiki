# Operational Loop Architecture Report

Phase C9 adds an operational layer above BBC-AOS agents. It does not modify core agents,
mathematical engines, or direct agent communication. The layer owns loop mode, state,
budget, pattern registry, run log, readiness audit, metrics, and kill switch files under
`.bbc/loop/`.
