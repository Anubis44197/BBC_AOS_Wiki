"""Timeline note generation for BBC Knowledge Vault."""

from typing import Any, Dict, Iterable


class TimelineGenerator:
    """Builds a chronological execution timeline."""

    def generate(self, executions: Iterable[Dict[str, Any]]) -> str:
        lines = ["# BBC Timeline", ""]
        for item in sorted(executions, key=lambda x: str(x.get("date", "")), reverse=True):
            date = item.get("date", "unknown")
            goal = item.get("goal") or item.get("goal_description") or "execution"
            status = item.get("status", "UNKNOWN")
            lines.append(f"- {date}: {goal} - {status}")
        lines.append("")
        return "\n".join(lines)
