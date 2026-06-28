"""BBC-AOS local security policy management."""

import json
from pathlib import Path
from typing import Any, Dict

from bbc_aos.runtime_paths import runtime_file


DEFAULT_POLICY: Dict[str, Any] = {
    "max_files_per_commit": 5,
    "require_tests": False,
    "auto_approve_low_risk": False,
    "blocked_paths": [".env", "secrets/", "credentials/"],
}


class PolicyEngine:
    """Loads and initializes `.bbc/policy.json`."""

    def __init__(self, project_root: str = ".") -> None:
        self.project_root = Path(project_root)
        self.policy_path = runtime_file(self.project_root, "policy.json")

    def ensure_policy(self) -> Dict[str, Any]:
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.policy_path.exists():
            self.policy_path.write_text(
                json.dumps(DEFAULT_POLICY, indent=2),
                encoding="utf-8",
            )
            return dict(DEFAULT_POLICY)
        return self.load_policy()

    def load_policy(self) -> Dict[str, Any]:
        try:
            data = json.loads(self.policy_path.read_text(encoding="utf-8"))
        except Exception:
            return dict(DEFAULT_POLICY)
        policy = dict(DEFAULT_POLICY)
        if isinstance(data, dict):
            policy.update(data)
        return policy
