"""
BBC Background Daemon
Arkaplanda sürekli BBC monitoring ve proje adaptasyonu
"""

import os
import sys

# Force UTF-8 encoding for standard streams on Windows to prevent UnicodeEncodeError
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

import time
import json
import signal
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class BBCDaemon:
    """BBC Background Daemon"""
    
    def __init__(self, project_root: str = None):
        self.running = False
        # Resolve .bbc/ relative to project root, not CWD
        if project_root:
            self.bbc_dir = Path(project_root).resolve() / ".bbc"
        else:
            # Default: script directory (repo root where bbc_daemon.py lives)
            self.bbc_dir = Path(__file__).resolve().parent / ".bbc"
        self.bbc_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.bbc_dir / "daemon.pid"
        self.log_file = self.bbc_dir / "daemon.log"
        self.config_file = self.bbc_dir / "config.json"
        
        # Signal handler'ları ayarla
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Daemon sinyal handler'ı"""
        self._log(f"Received signal {signum}. Shutting down...")
        self.stop()
    
    def _log(self, message: str):
        """Daemon log'u yaz"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception:
            pass  # Silent fail for daemon
    
    def _write_pid(self):
        """PID dosyasını yaz"""
        try:
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass
    
    def _remove_pid(self):
        """PID dosyasını sil"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass
    
    def _is_running(self) -> bool:
        """Daemon'ın çalışıp çalışmadığını kontrol et"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            if os.name == 'nt':
                import ctypes
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except (OSError, ValueError):
            return False
    
    def start(self, project_path: str = ".", auto_detect: bool = True):
        """Daemon'ı başlat"""
        # Re-anchor .bbc/ to the target project if provided
        resolved_project = Path(project_path).resolve()
        self.bbc_dir = resolved_project / ".bbc"
        self.bbc_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.bbc_dir / "daemon.pid"
        self.log_file = self.bbc_dir / "daemon.log"
        self.config_file = self.bbc_dir / "config.json"

        if self._is_running():
            print("BBC Daemon is already running")
            return False
        
        # Fork işlemi (Unix/Linux için)
        if os.name != 'nt':
            try:
                pid = os.fork()
                if pid > 0:
                    # Parent process - exit
                    print(f"BBC Daemon started with PID: {pid}")
                    return True
            except OSError:
                pass  # Fork başarısız, foreground'da çalıştır
        
        # Daemon process
        os.environ["BBC_DAEMON"] = "1"
        self.running = True
        self._write_pid()
        
        # Working directory'i ayarla
        os.chdir(Path(project_path).resolve())
        
        # Standart I/O'yu yönlendir
        sys.stdout.flush()
        sys.stderr.flush()
        
        self._log("BBC Daemon started")
        self._log(f"Project path: {Path(project_path).resolve()}")
        self._log(f"Auto-detect: {auto_detect}")
        
        try:
            self._run_daemon_loop(project_path, auto_detect)
        except Exception as e:
            self._log(f"Daemon error: {e}")
        finally:
            self._remove_pid()
            self._log("BBC Daemon stopped")
    
    def stop(self):
        """Daemon'ı durdur"""
        if not self.pid_file.exists():
            print("BBC Daemon is not running")
            return False
        
        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            if os.name == 'nt':
                import subprocess
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
                
                for _ in range(10):
                    try:
                        os.kill(pid, 0)
                        time.sleep(0.5)
                    except OSError:
                        break
                else:
                    os.kill(pid, signal.SIGKILL)
            
            self._remove_pid()
            print("BBC Daemon stopped")
            return True
            
        except Exception as e:
            print(f"Failed to stop BBC Daemon: {e}")
            return False
    
    def status(self):
        """Daemon durumunu göster"""
        if self._is_running():
            print("[OK] BBC Daemon is running")
            
            # Config dosyasından durum bilgilerini oku
            if self.config_file.exists():
                try:
                    with open(self.config_file, "r") as f:
                        config = json.load(f)
                    
                    print(f"Project: {config.get('project_path', 'Unknown')}")
                    print(f"Status: {config.get('status', 'Unknown')}")
                    print(f"Started: {config.get('start_time', 'Unknown')}")
                    
                except Exception:
                    pass
        else:
            print("[ERR] BBC Daemon is not running")
    
    def _scan_project_files(self, project_path: Path) -> set:
        """Projedeki kaynak dosyalarını tara, relative path set'i döndür"""
        exts = ('.py', '.md', '.json', '.js', '.jsx', '.ts', '.tsx', '.html', '.css',
                '.sql', '.rs', '.go', '.c', '.cpp', '.h', '.hpp', '.java', '.cs',
                '.php', '.rb', '.swift', '.kt')
        forbidden_dirs = {'node_modules', '.venv', 'dist', 'build', '.git', '__pycache__', 'target', '.bbc'}
        found = set()
        try:
            for root, dirs, files in os.walk(str(project_path)):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in forbidden_dirs]
                for f in files:
                    if f.lower().endswith(exts):
                        rel = os.path.relpath(os.path.join(root, f), str(project_path))
                        found.add(rel)
        except Exception:
            pass
        return found

    def _run_reanalysis(self, project_path: str) -> bool:
        """Projeyi in-process yeniden analiz et ve AI config'lerini inject et (hızlı: <100ms)"""
        try:
            import asyncio
            import os
            from bbc_core.cli import BBCCLI
            from bbc_core.agent_adapter import inject_to_project
            
            project_path_abs = os.path.abspath(project_path)
            ctx_path = self.bbc_dir / "bbc_context.json"
            
            cli = BBCCLI()
            
            # Incremental analysis runs in <10ms in-process
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    cli.run_analysis_incremental(project_path_abs, str(ctx_path), silent=True),
                    loop
                )
                context = future.result(timeout=10)
            else:
                context = loop.run_until_complete(
                    cli.run_analysis_incremental(project_path_abs, str(ctx_path), silent=True)
                )
            
            # In-process injection runs in <2ms when passing preloaded context
            inject_to_project(context, project_path_abs, optimize=True, active_command="inject")
            self._log("In-process re-analysis and rules injection completed")
            return True
        except Exception as e:
            self._log(f"In-process Re-analysis error: {e}. Falling back to subprocess...")
            return self._run_reanalysis_subprocess(project_path)

    def _run_reanalysis_subprocess(self, project_path: str) -> bool:
        """Fallback to subprocess run"""
        import subprocess as sp
        run_bbc = Path(__file__).resolve().parent / "run_bbc.py"
        if not run_bbc.exists():
            self._log(f"run_bbc.py not found at {run_bbc}")
            return False
        try:
            sp.run([sys.executable, str(run_bbc), "analyze", project_path, "--incremental", "--silent"],
                   capture_output=True, text=True, timeout=120)
            sp.run([sys.executable, str(run_bbc), "inject", project_path, "--silent"],
                   capture_output=True, text=True, timeout=60)
            self._log("Subprocess re-analysis and rules injection completed")
            return True
        except Exception as e:
            self._log(f"Subprocess Re-analysis error: {e}")
            return False

    def _run_daemon_loop(self, project_path: str, auto_detect: bool):
        """Ana daemon döngüsü — dosya değişikliği/eklenmesi/silinmesi algılar"""
        project_path = Path(project_path).resolve()
        project_str = str(project_path)
        last_project = None
        bbc_active = False
        
        # File watcher state
        known_files = set()  # bilinen dosya seti
        mtime_cache = {}     # file path -> modification time cache
        
        # BBC modüllerini import et
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        
        def update_mtime_cache(files):
            for f in files:
                fp = project_path / f
                try:
                    mtime_cache[f] = fp.stat().st_mtime
                except Exception:
                    mtime_cache[f] = 0.0
        
        try:
            from bbc_core.auto_detector import get_auto_detector
            from bbc_core.ide_hooks import get_ide_hooks
            
            detector = get_auto_detector()
            ide_hooks = get_ide_hooks()
            
            # İlk dosya listesini al
            ctx_path = self.bbc_dir / "bbc_context.json"
            if ctx_path.exists():
                try:
                    with open(ctx_path, "r", encoding="utf-8") as f:
                        ctx_data = json.load(f)
                    known_files = {item.get("path", "") for item in ctx_data.get("code_structure", []) if isinstance(item, dict)}
                    self._log(f"Initial file set loaded: {len(known_files)} files")
                except Exception as e:
                    self._log(f"Failed to load initial context: {e}")
            
            if not known_files:
                known_files = self._scan_project_files(project_path)
                self._log(f"Initial scan: {len(known_files)} files")
            
            update_mtime_cache(known_files)
            
            while self.running:
                try:
                    current_dir = Path.cwd()
                    
                    # Proje değişikliği kontrol et
                    if current_dir != last_project:
                        if last_project:
                            self._log(f"Project changed: {last_project.name} -> {current_dir.name}")
                            if bbc_active:
                                detector.stop_bbc_monitoring()
                                ide_hooks.stop_monitoring()
                                bbc_active = False
                        
                        if auto_detect:
                            self._log(f"Auto-detecting new project: {current_dir.name}")
                            if detector.auto_detect_and_start():
                                ide_hooks.auto_setup_ide_integration(current_dir)
                                bbc_active = True
                                self._update_config(current_dir, "ACTIVE")
                        
                        last_project = current_dir
                    
                    # === FILE WATCHER: Fast modification timestamp check ===
                    current_files = self._scan_project_files(project_path)
                    new_files = current_files - known_files
                    deleted_files = known_files - current_files
                    
                    needs_reanalysis = False
                    reason = ""
                    
                    if new_files:
                        reason = f"new files: {list(new_files)[:3]}"
                        needs_reanalysis = True
                    elif deleted_files:
                        reason = f"deleted files: {list(deleted_files)[:3]}"
                        needs_reanalysis = True
                    else:
                        for f in current_files:
                            fp = project_path / f
                            try:
                                mtime = fp.stat().st_mtime
                                if f not in mtime_cache or mtime > mtime_cache[f]:
                                    reason = f"modified file: {f}"
                                    needs_reanalysis = True
                                    break
                            except Exception:
                                pass
                                
                    if needs_reanalysis:
                        self._log(f"[WATCH] Change detected ({reason}). Triggering fast in-process re-analysis.")
                        start_time = time.time()
                        success = self._run_reanalysis(project_str)
                        elapsed = (time.time() - start_time) * 1000
                        self._log(f"[WATCH] Re-analysis completed in {elapsed:.1f}ms (success: {success})")
                        
                        # Update cached values
                        known_files = current_files
                        update_mtime_cache(current_files)
                        
                        # Aura Gradient Bend — HMPU feedback
                        try:
                            from bbc_core.hmpu_core import HMPU_Governor
                            governor = HMPU_Governor()
                            if success:
                                governor.aura_gradient_bend(delta=0.05, stability=True)
                            else:
                                governor.aura_gradient_bend(delta=0.1, stability=False)
                        except Exception:
                            pass
                            
                        if success:
                            self._update_config(project_path, "RESEALED")
                    else:
                        known_files = current_files
                    
                    # Poll file system changes every 200ms
                    time.sleep(0.2)
                    
                except Exception as e:
                    self._log(f"Loop error: {e}")
                    time.sleep(1.0)
        except ImportError as e:
            self._log(f"Failed to import BBC modules: {e}")
            self._log("Make sure BBC is properly installed")
    
    def _update_config(self, project_path: Path, status: str):
        """Config dosyasını güncelle"""
        config = {
            "project_path": str(project_path),
            "status": status,
            "start_time": datetime.now().isoformat(),
            "timestamp": time.time()
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self._log(f"Failed to update config: {e}")

def main():
    """Daemon CLI fonksiyonu"""
    if len(sys.argv) < 2:
        print("Usage: python bbc_daemon.py [start|stop|status] [project_path]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    project_path = sys.argv[2] if len(sys.argv) > 2 else "."
    
    daemon = BBCDaemon(project_root=project_path)
    
    if command == "start":
        daemon.start(project_path)
    elif command == "stop":
        daemon.stop()
    elif command == "status":
        daemon.status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
