import os
import sqlite3
import time
from typing import List, Dict, Any, Tuple
from bbc_core.config import BBCConfig

class MemoryStore:
    """BBC Episodic Memory Store - Saves and recalls user preferences and decisions."""

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        bbc_dir = BBCConfig.get_bbc_dir(self.project_root)
        self.db_path = os.path.join(bbc_dir, "memory.db")
        self.md_path = os.path.join(bbc_dir, "BBC_MEMORY.md")
        self._ensure_db()

    def _ensure_db(self):
        """Ensure database and table exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def remember(self, topic: str, content: str, force: bool = False) -> Tuple[bool, str]:
        """Save a memory/decision with conflict detection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check for conflict
            if not force:
                cursor.execute('SELECT content FROM memories WHERE topic = ?', (topic.strip(),))
                existing = cursor.fetchone()
                if existing:
                    conn.close()
                    return False, f"CONFLICT: A memory for '{topic}' already exists ('{existing[0]}'). Use --force to overwrite."

            if force:
                cursor.execute('DELETE FROM memories WHERE topic = ?', (topic.strip(),))

            cursor.execute('''
                INSERT INTO memories (topic, content, timestamp)
                VALUES (?, ?, ?)
            ''', (topic.strip(), content.strip(), time.time()))

            conn.commit()
            conn.close()
            self._export_to_md()
            return True, "Success"
        except Exception as e:
            print(f"[ERR] BBC Memory Error: {e}")
            return False, str(e)

    def recall(self, query: str) -> List[Dict[str, Any]]:
        """Recall memories matching the query (topic or content)."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            search_query = f"%{query.strip()}%"
            cursor.execute('''
                SELECT topic, content, timestamp
                FROM memories
                WHERE topic LIKE ? OR content LIKE ?
                ORDER BY timestamp DESC
            ''', (search_query, search_query))
            rows = cursor.fetchall()
            conn.close()

            return [{"topic": r["topic"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]
        except Exception as e:
            print(f"[ERR] BBC Memory Error: {e}")
            return []

    def _export_to_md(self):
        """Export all memories to a structured markdown file."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic, content, timestamp
                FROM memories
                ORDER BY topic ASC, timestamp DESC
            ''')
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return

            from datetime import datetime

            # Group by topic
            memories_by_topic = {}
            for r in rows:
                topic = r["topic"]
                if topic not in memories_by_topic:
                    memories_by_topic[topic] = []
                memories_by_topic[topic].append(r)

            lines = []
            lines.append("# BBC Episodic Memory")
            lines.append("")
            lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
            lines.append(f"> Total memories: **{len(rows)}**  ")
            lines.append("")
            lines.append("---")
            lines.append("")

            for topic, mems in memories_by_topic.items():
                lines.append(f"## {topic}")
                lines.append("")
                for mem in mems:
                    dt = datetime.fromtimestamp(mem["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
                    lines.append(f"### [Recorded: {dt}]")
                    lines.append(f"{mem['content']}")
                    lines.append("")
                lines.append("---")
                lines.append("")

            with open(self.md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        except Exception as e:
            print(f"[ERR] BBC Memory Export Error: {e}")
