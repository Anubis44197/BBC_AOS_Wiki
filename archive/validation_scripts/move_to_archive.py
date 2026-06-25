import os
import shutil
import glob

workspace = r"C:\Users\90535\.gemini\antigravity\scratch\BBC_AOS_Wiki"

def safe_move(src, dst_dir):
    if not os.path.exists(src):
        return
    os.makedirs(dst_dir, exist_ok=True)
    try:
        shutil.move(src, dst_dir)
        print(f"[MOVE] {os.path.basename(src)} -> {dst_dir}")
    except Exception as e:
        print(f"[ERR] Failed to move {src} to {dst_dir}: {e}")

# 1. Move Legacy_BBC and Specs
safe_move(os.path.join(workspace, "Legacy_BBC"), os.path.join(workspace, "archive", "legacy_bbc"))
safe_move(os.path.join(workspace, "Specs"), os.path.join(workspace, "archive", "old_specs"))

# 2. Move root markdown documents
docs_to_move = [
    "implementation_plan.md",
    "repository_inventory.md",
    "spec_inventory.md",
    "task.md",
    "walkthrough.md"
]
for doc in docs_to_move:
    safe_move(os.path.join(workspace, doc), os.path.join(workspace, "archive", "historical_docs"))

# 3. Move old validation scripts from scratch
validation_patterns = [
    "validate_phase*.py",
    "debug_run.py",
    "debug_violations.py"
]
for pattern in validation_patterns:
    for f in glob.glob(os.path.join(workspace, "scratch", pattern)):
        safe_move(f, os.path.join(workspace, "archive", "validation_scripts"))

# 4. Move old certification data if exists
safe_move(os.path.join(workspace, "scratch", "certification_data"), os.path.join(workspace, "archive", "certification_data"))
safe_move(os.path.join(workspace, "scratch", "golden_master"), os.path.join(workspace, "archive", "certification_data"))

# 5. Move reports to archive/phase_reports and archive/migration_reports
migration_report_keywords = [
    "migration_phase", "migration_report", "migration_sequence", "legacy_to_aos",
    "equivalence", "reduction", "packer", "extraction"
]

reports_dir = os.path.join(workspace, "Reports")
if os.path.exists(reports_dir):
    for f in os.listdir(reports_dir):
        src_path = os.path.join(reports_dir, f)
        if os.path.isfile(src_path):
            is_migration = any(kw in f for kw in migration_report_keywords)
            if is_migration:
                safe_move(src_path, os.path.join(workspace, "archive", "migration_reports"))
            else:
                safe_move(src_path, os.path.join(workspace, "archive", "phase_reports"))

# 6. Clean up old/unused python files in src/bbc_aos/ that are not part of core layout
# E.g. requirements.txt, pyproject.toml inside src/bbc_aos/
safe_move(os.path.join(workspace, "src", "bbc_aos", "requirements.txt"), os.path.join(workspace, "archive", "historical_docs"))
safe_move(os.path.join(workspace, "src", "bbc_aos", "pyproject.toml"), os.path.join(workspace, "archive", "historical_docs"))
safe_move(os.path.join(workspace, "src", "bbc_aos", "README.md"), os.path.join(workspace, "archive", "historical_docs"))

print("[*] Archiving completed successfully!")
