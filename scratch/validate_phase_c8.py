"""Stdlib validation checks for Phase C8."""

import tempfile
from pathlib import Path

from bbc_aos.agents.reflection_agent import ReflectionAgent
from bbc_aos.audit.loop_audit import LoopAudit
from bbc_aos.memory.failure_memory import FailureMemory
from bbc_aos.security.invariant_engine import InvariantEngine
from bbc_aos.wiki.reflection_generator import ReflectionGenerator
from tools.benchmark_real_repositories import run_benchmark


def validate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agent = ReflectionAgent()
        params = {"context": {"goal": "fix jwt", "outputs": {"verify_result": {"verdict": "APPROVED"}}}}
        first = agent.execute(params)
        second = agent.execute(params)
        assert first["deterministic_hash"] == second["deterministic_hash"]

        memory = FailureMemory(str(root))
        memory.record_failure("tr1", "MISSING_IMPORT", "jwt import missing", ["auth/login.py"])
        repeated = memory.record_failure("tr2", "MISSING_IMPORT", "jwt import missing", ["auth/login.py"])
        assert repeated["occurrence_count"] == 2

        invariants = InvariantEngine(str(root))
        invariants.ensure_config()
        blocked = invariants.validate(["settings.py"], "+import subprocess\n")
        assert not blocked["allowed"]

        project = root / "BBC_KNOWLEDGE" / "Projects" / "demo"
        note = ReflectionGenerator().write(project, "fix jwt", first, ["auth/login.py"], "rp1")
        assert note.exists()

        benchmark = run_benchmark(str(root / "benchmark_results.json"))
        assert len(benchmark["rows"]) == 10

        audit = LoopAudit(str(root)).summary()
        assert "executions" in audit


if __name__ == "__main__":
    validate()
    print("phase_c8_validation=PASS")
