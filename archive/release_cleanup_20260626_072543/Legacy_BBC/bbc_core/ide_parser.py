import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Tuple


class IDETokenParser:
    """
    Reads observed token/character usage from supported IDE data stores.
    Calibration must never use synthetic placeholder values.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.appdata = os.environ.get("APPDATA", "")
        self.localappdata = os.environ.get("LOCALAPPDATA", "")

    def _parse_cursor_db(self) -> Optional[Dict[str, int]]:
        """Read Cursor's state.vscdb chat data and estimate token usage."""
        if not self.appdata:
            return None

        db_path = Path(self.appdata) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
        try:
            if not db_path.exists():
                return None

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM ItemTable "
                "WHERE key = 'workbench.panel.aichat.view.aichat.chatdata'"
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            data = json.loads(row[0])
            tabs = data.get("tabs", [])

            total_input_chars = 0
            total_output_chars = 0
            message_count = 0
            last_model = "unknown"

            for tab in tabs:
                for bubble in tab.get("bubbles", []):
                    text = bubble.get("text", "")
                    if bubble.get("type") == "ai":
                        total_output_chars += len(text)
                        message_count += 1
                        if bubble.get("modelType"):
                            last_model = bubble.get("modelType")
                    elif bubble.get("type") == "user":
                        total_input_chars += len(text)
                        message_count += 1

            input_tokens = total_input_chars // 4
            output_tokens = total_output_chars // 4

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "total_chars": total_input_chars + total_output_chars,
                "message_count": message_count,
                "model": last_model,
                "source": "Cursor (state.vscdb)",
            }
        except Exception:
            return None

    def _parse_vscode_db(self) -> Optional[Dict[str, int]]:
        """VSCode/Copilot parsing is not implemented yet."""
        return None

    def _parse_windsurf_db(self) -> Optional[Dict[str, int]]:
        """Windsurf parsing is not implemented yet."""
        return None

    def supported_sources(self) -> Dict[str, Dict[str, str]]:
        """Return parser support status without reading private IDE databases."""
        return {
            "cursor": {
                "status": "real_usage_supported",
                "source": "Cursor/User/globalStorage/state.vscdb",
            },
            "vscode": {
                "status": "safe_fallback",
                "source": "No stable local token database parser implemented",
            },
            "windsurf": {
                "status": "safe_fallback",
                "source": "No stable local token database parser implemented",
            },
        }

    def get_real_usage(self, ide_name: str) -> Tuple[bool, str, Dict[str, int]]:
        """
        Read token usage for the requested IDE.
        Returns: (success, message, data)
        """
        ide_name = ide_name.lower()

        if ide_name == "cursor":
            data = self._parse_cursor_db()
            if data:
                return True, "Cursor database read successfully.", data
            return False, "Cursor database not found or empty.", {}

        if ide_name in ("vscode", "visualstudio"):
            data = self._parse_vscode_db()
            if data:
                return True, "VSCode Copilot usage analyzed.", data
            return False, "VSCode Copilot usage not found or parser is not implemented yet.", {}

        if ide_name == "windsurf":
            data = self._parse_windsurf_db()
            if data:
                return True, "Windsurf usage analyzed.", data
            return False, "Windsurf usage not found or parser is not implemented yet.", {}

        return False, f"Unsupported IDE: {ide_name}", {}
