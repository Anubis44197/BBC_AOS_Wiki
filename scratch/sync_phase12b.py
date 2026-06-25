import shutil
import os

brain_dir = r"C:\Users\90535\.gemini\antigravity\brain\af9c3fab-d929-4fa5-983e-c6a18632dcc0"
workspace_dir = r"C:\Users\90535\.gemini\antigravity\scratch\BBC_AOS_Wiki"
desktop_dir = r"C:\Users\90535\Desktop\BBC_AOS_Wiki"

# 1. Synchronize pilot scripts and metrics
scripts = [
    "run_ide_pilot.py",
    "sync_phase12b.py",
    "ide_pilot_metrics.json"
]
for s in scripts:
    src_val = os.path.join(workspace_dir, "scratch", s)
    if os.path.exists(src_val):
        desktop_val = os.path.join(desktop_dir, "scratch", s)
        os.makedirs(os.path.dirname(desktop_val), exist_ok=True)
        shutil.copy2(src_val, desktop_val)
        print(f"Synced script/metric {s} to Desktop.")

# 2. Synchronize reports from brain to workspace Reports/ and Desktop Reports/
reports = [
    "ide_pilot_report.md",
    "ide_determinism_report.md",
    "ide_replay_report.md",
    "ide_user_interaction_report.md",
    "ide_final_certification.md"
]

for filename in reports:
    src_report = os.path.join(brain_dir, filename)
    if os.path.exists(src_report):
        dst_ws = os.path.join(workspace_dir, "Reports", filename)
        dst_dt = os.path.join(desktop_dir, "Reports", filename)
        os.makedirs(os.path.dirname(dst_ws), exist_ok=True)
        os.makedirs(os.path.dirname(dst_dt), exist_ok=True)
        shutil.copy2(src_report, dst_ws)
        shutil.copy2(src_report, dst_dt)
        print(f"Synced report {filename} to workspace and Desktop.")

# 3. Synchronize task.md and walkthrough.md
roots = ["task.md", "walkthrough.md"]
for filename in roots:
    src_root = os.path.join(workspace_dir, filename)
    if os.path.exists(src_root):
        shutil.copy2(src_root, os.path.join(desktop_dir, filename))
        print(f"Synced root file {filename} to Desktop.")

print("Phase 12B sync operations completed successfully!")
