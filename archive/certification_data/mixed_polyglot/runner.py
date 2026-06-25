#!/usr/bin/env python
import os
import sys
import json

def load_settings():
    path = os.path.join(os.path.dirname(__file__), "settings.json")
    if not os.path.exists(path):
        return {"env": "development", "debug": True}
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    settings = load_settings()
    print(f"MIXED POLYGLOT RUNNER INITIALIZED. ENV={settings.get('env')}")
