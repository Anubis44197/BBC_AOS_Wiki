import shutil
import os

brain_dir = r"C:\Users\90535\.gemini\antigravity\brain\af9c3fab-d929-4fa5-983e-c6a18632dcc0"
workspace_dir = r"C:\Users\90535\.gemini\antigravity\scratch\BBC_AOS_Wiki"
desktop_dir = r"C:\Users\90535\Desktop\BBC_AOS_Wiki"

# 1. Synchronize sync script itself
shutil.copy2(os.path.join(workspace_dir, "scratch", "sync_phase13a.py"), os.path.join(desktop_dir, "scratch", "sync_phase13a.py"))
print("Synced sync_phase13a.py to Desktop.")

# 2. Synchronize reports from brain to workspace Reports/ and Desktop Reports/
reports = [
    "repository_cleanup_plan.md",
    "production_repository_structure.md",
    "archive_candidates.md",
    "repository_migration_plan.md",
    "cli_user_guide.md",
    "cli_command_reference.md",
    "hallucination_benchmark_plan.md",
    "token_reduction_benchmark_plan.md",
    "production_eval_strategy.md",
    "obsidian_user_guide.md",
    "obsidian_configuration_reference.md",
    "packaging_strategy.md",
    "docker_deployment_strategy.md",
    "release_checklist.md"
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

# 3. Synchronize README.md, task.md, walkthrough.md
roots = ["README.md", "task.md", "walkthrough.md"]
for filename in roots:
    src_root = os.path.join(workspace_dir, filename)
    if os.path.exists(src_root):
        shutil.copy2(src_root, os.path.join(desktop_dir, filename))
        print(f"Synced root file {filename} to Desktop.")

print("Phase 13A sync operations completed successfully!")
