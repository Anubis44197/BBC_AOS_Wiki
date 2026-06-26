"""Phase C9 validation script."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from bbc_aos.operations import LoopManager


def main() -> None:
    root = Path(tempfile.mkdtemp())
    manager = LoopManager(root)
    manager.init()
    manager.set_mode("l1")
    manager.set_mode("l2")
    readiness = manager.audit()
    patterns = manager.patterns()
    state = manager.start("security_scan")
    manager.budget_store.record_execution(runtime_ms=10, tokens_saved=100)
    manager.kill()
    result = {
        "mode": manager.status()["mode"],
        "readiness_score": readiness["readiness_score"],
        "patterns": len(patterns),
        "state": state["status"],
        "history": len(manager.history()),
        "metrics": manager.metrics(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
