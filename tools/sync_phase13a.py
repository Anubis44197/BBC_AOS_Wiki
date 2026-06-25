import os
import shutil

brain_dir = r"C:\Users\90535\.gemini\antigravity\brain\af9c3fab-d929-4fa5-983e-c6a18632dcc0"
workspace_dir = r"C:\Users\90535\.gemini\antigravity\scratch\BBC_AOS_Wiki"
desktop_dir = r"C:\Users\90535\Desktop\BBC_AOS_Wiki"

def sync_directories(src_dir, dst_dir):
    """Recursively copies files and folders from src to dst, ignoring cache files."""
    if not os.path.exists(src_dir):
        return
    os.makedirs(dst_dir, exist_ok=True)
    
    ignore_patterns = {".git", ".pytest_cache", "__pycache__", ".pytest-tmp", ".bbc"} # Keep .bbc local runtime data out of desktop sync
    
    for item in os.listdir(src_dir):
        if item in ignore_patterns:
            continue
            
        src_path = os.path.join(src_dir, item)
        dst_path = os.path.join(dst_dir, item)
        
        if os.path.isdir(src_path):
            if os.path.exists(dst_path):
                # Clean up existing directory on destination to avoid stale files
                import stat
                def remove_readonly(func, path, excinfo):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        pass
                try:
                    shutil.rmtree(dst_path, onexc=remove_readonly)
                except TypeError:
                    shutil.rmtree(dst_path, onerror=remove_readonly)
            shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".pytest-tmp"))
            print(f"[SYNC DIR] {item}")
        else:
            shutil.copy2(src_path, dst_path)
            print(f"[SYNC FILE] {item}")

def main():
    print("=" * 60)
    print("BBC-AOS Workspace Synchronization Tool")
    print("=" * 60)

    # 1. First sync brain artifacts (implementation_plan.md, task.md, walkthrough.md) to workspace archive
    brain_docs = ["implementation_plan.md", "task.md", "walkthrough.md"]
    ws_archive_docs = os.path.join(workspace_dir, "archive", "historical_docs")
    os.makedirs(ws_archive_docs, exist_ok=True)
    
    for doc in brain_docs:
        src_doc = os.path.join(brain_dir, doc)
        if os.path.exists(src_doc):
            shutil.copy2(src_doc, os.path.join(ws_archive_docs, doc))
            print(f"[SYNC BRAIN DOC] {doc} -> workspace archive")

    # 2. Sync workspace root to Desktop recursively
    sync_directories(workspace_dir, desktop_dir)
    print("\n[*] Workspace sync to Desktop completed successfully!")

if __name__ == "__main__":
    main()
