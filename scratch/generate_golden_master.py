import os
import sys
import json
import asyncio

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_ROOT = os.path.dirname(SCRATCH_DIR)

sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

from bbc_core.hmpu_engine import HMPUEngine
from bbc_core.state_manager import StateManager

# Setup directories
GM_DIR = os.path.join(SCRATCH_DIR, "golden_master")
os.makedirs(GM_DIR, exist_ok=True)

# Datasets
datasets = {
    "code": """
import os
import sys
from collections import Counter

class DataProcessor:
    def __init__(self, size: int) -> None:
        self.size = size
        
    def filter_data(self, data: list) -> list:
        return [x for x in data if x is not None]

def global_handler(item):
    print("handling", item)
""",
    "log": """
2026-06-24 12:00:00 INFO Initializing database connections.
2026-06-24 12:00:01 WARNING High memory threshold warning.
2026-06-24 12:00:02 ERROR Failed to bind socket.
2026-06-24 12:00:03 CRITICAL EXCEPTION: connection timeout.
2026-06-24 12:00:04 DEBUG Connection closed.
""",
    "config": """
{
  "project_name": "BBC-AOS",
  "version": "1.0.0",
  "settings": {
    "debug": true,
    "max_connections": 100,
    "services": ["database", "redis", "gateway"]
  }
}
""",
    "doc": """
# Project Documentation

This is the documentation for the BBC-AOS project.

## 1. Overview
The orchestrator drives execution.

## 2. Resources
Visit our portal at http://example.com/portal or contact support.
""",
    "hybrid": """
--- FILE: main.py ---
import os
def main():
    print("AOS run")

--- FILE: README.md ---
# Hybrid Pipeline Test
This is a documentation section within a hybrid multi-file source stream.
"""
}

async def generate():
    # Save input files
    for name, content in datasets.items():
        ext = ".py" if name == "code" else ".log" if name == "log" else ".json" if name == "config" else ".md" if name == "doc" else ".txt"
        file_path = os.path.join(GM_DIR, f"input_{name}{ext}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
    # Reset state manager
    StateManager._reset_for_testing()
    sm = StateManager()
    engine = HMPUEngine(sm)
    
    # Run each through legacy engine and save JSON outputs
    for name, content in datasets.items():
        result = await engine.create_recipe(content.strip())
        
        # Save output JSON
        out_path = os.path.join(GM_DIR, f"output_{name}_legacy.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"[+] Saved Golden Master for {name}")

if __name__ == "__main__":
    asyncio.run(generate())
