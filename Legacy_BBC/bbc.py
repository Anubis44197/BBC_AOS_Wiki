#!/usr/bin/env python3
"""
BBC CLI - User-Friendly Interface v8.6
Single command BBC launcher: bbc start
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
import argparse
import signal
import subprocess
import time
import json
import re
from pathlib import Path
import tempfile
import shutil

# Add BBC modules to path
sys.path.append(str(Path(__file__).parent))

from bbc_core.auto_detector import auto_start_bbc, stop_bbc_auto

BBC_VERSION = "8.6.0"

BBC_RULE_INVARIANTS = {
    "sealed_context": ["sealed", "context"],
    "no_hallucination": ["hallucinat"],
    "reuse_first": ["reuse-first", "reuse verified"],
}

SECRET_PATTERNS = {
    "credential_assignment": re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=\-]{12,}"
    ),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_./+=\-]{20,}"),
    "private_key": re.compile(r"(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

SECURITY_SCAN_EXTENSIONS = {
    ".env",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".ps1",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SECURITY_SKIP_DIRS = {
    ".bbc",
    ".git",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "tests",
    "venv",
    ".venv",
}


def _update_context_freshness(ctx_file: str, fresh: bool) -> None:
    """Update the context_fresh field in bbc_context.json."""
    try:
        with open(ctx_file, "r", encoding="utf-8") as f:
            ctx = json.load(f)
        ctx["context_fresh"] = fresh
        with open(ctx_file, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _print_transaction_report(project_path: str, source: str) -> None:
    """Print BBC token savings / aura report after a completed operation."""
    try:
        from bbc_core.config import BBCConfig

        project_resolved = str(Path(project_path).resolve())
        ctx_file = BBCConfig.get_context_path(project_resolved)

        if os.path.exists(ctx_file):
            try:
                with open(ctx_file, "r", encoding="utf-8") as f:
                    ctx = json.load(f)
                ctx.setdefault("metrics", {})
                ctx["metrics"]["unified_status"] = "COMPLETED"
                ctx["metrics"]["unified_source"] = source
                ctx["metrics"]["unified_updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                with open(ctx_file, "w", encoding="utf-8") as f:
                    json.dump(ctx, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        if not os.path.exists(ctx_file):
            return

        with open(ctx_file, "r", encoding="utf-8") as f:
            ctx = json.load(f)

        metrics = ctx.get("metrics", {})
        raw_tokens = int(metrics.get("raw_tokens") or 0)
        context_tokens = int(metrics.get("context_tokens") or 0)
        tokens_saved = int(metrics.get("unified_tokens_saved") or max(raw_tokens - context_tokens, 0))
        savings_pct = metrics.get("unified_savings_pct", metrics.get("savings_pct", 0.0))

        try:
            savings_pct = float(savings_pct)
        except (TypeError, ValueError):
            savings_pct = 0.0

        print(f"[BBC v8.6] STABLE | Savings: {savings_pct:.1f}% | Saved: {tokens_saved:,} Tokens")
    except Exception as e:
        print(f"[BBC] Report error: {e}")


class BBCCLI:
    """BBC Command Line Interface v8.6"""

    def __init__(self):
        self.running = False
        self.script_dir = Path(__file__).parent
        self.run_bbc_script = self.script_dir / "run_bbc.py"

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        sys.exit(0)

    def run_command(self, cmd_args):
        """Helper to run run_bbc.py commands"""
        return subprocess.call([sys.executable, str(self.run_bbc_script)] + cmd_args)

    def init(self, project_path: str = ".", force: bool = False, no_inject: bool = False):
        """Initialize BBC for a project without starting the daemon/watch loop."""
        project_resolved = str(Path(project_path).resolve())
        print(f"[BBC] Initializing project: {project_resolved}")

        analyze_cmd = ["analyze", project_resolved]
        if force:
            print("[BBC] Force refresh requested.")
        if self.run_command(analyze_cmd) != 0:
            print("[BBC] Init failed during analyze.")
            return 1

        if not no_inject:
            inject_cmd = ["inject", project_resolved, "--auto-analyze", "--silent"]
            if force:
                inject_cmd.append("--force")
            if self.run_command(inject_cmd) != 0:
                print("[BBC] Init failed during inject.")
                return 1
        else:
            print("[BBC] Inject skipped by --no-inject.")

        if self.run_command(["doctor", project_resolved]) != 0:
            print("[BBC] Init completed, but doctor reported warnings/errors.")
            return 1

        print("[BBC] Init complete. Project is ready for BBC-aware AI coding.")
        return 0

    def benchmark(self, project_path: str = ".", json_output: bool = False):
        """Report token reduction and guardrail readiness for a BBC project."""
        report = self._benchmark_report(project_path)
        if report.get("status") == "MISSING":
            print(f"[BBC] Context not found: {report['context_file']}")
            print(f"[BBC] Run 'bbc init {project_path}' or 'bbc analyze {project_path}' first.")
            return 1
        if report.get("status") == "ERROR":
            print(f"[BBC] Could not read context: {report.get('error')}")
            return 1

        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0

        print("\n" + "=" * 60)
        print(" BBC BENCHMARK")
        print("=" * 60)
        print(f"Project:          {report['project_root']}")
        print(f"Files scanned:    {report['files_scanned']}")
        print(f"Symbols:          {report['symbols_extracted']}")
        print(f"Normal tokens:    {report['normal_tokens']:,}")
        print(f"BBC tokens:       {report['bbc_tokens']:,}")
        print(f"Tokens avoided:   {report['tokens_avoided']:,}")
        print(f"Reduction:        {report['reduction_pct']:.1f}%")
        print(f"Context fresh:    {report['context_fresh']}")
        print(f"Seal status:      {report['constraint_status']}")
        print("=" * 60)
        return 0

    def _benchmark_report(self, project_path: str = "."):
        """Build token reduction and context readiness metrics."""
        project_resolved = Path(project_path).resolve()
        ctx_file = project_resolved / ".bbc" / "bbc_context.json"
        if not ctx_file.exists():
            return {
                "status": "MISSING",
                "project_root": str(project_resolved),
                "context_file": str(ctx_file),
            }

        try:
            with open(ctx_file, "r", encoding="utf-8") as f:
                ctx = json.load(f)
        except Exception as e:
            return {
                "status": "ERROR",
                "project_root": str(project_resolved),
                "context_file": str(ctx_file),
                "error": str(e),
            }

        metrics = ctx.get("metrics", {})
        skeleton = ctx.get("project_skeleton", ctx.get("skeleton", {}))
        code_structure = ctx.get("code_structure", [])
        file_count = int(metrics.get("files_scanned") or skeleton.get("file_count") or len(code_structure) or 0)
        symbol_count = 0
        for entry in code_structure:
            if isinstance(entry, dict):
                structure = entry.get("structure", entry)
                symbol_count += len(structure.get("classes", []) or [])
                symbol_count += len(structure.get("functions", []) or [])

        raw_tokens = int(metrics.get("raw_tokens") or metrics.get("unified_tokens_normal") or 0)
        context_tokens = int(metrics.get("context_tokens") or metrics.get("unified_tokens_used") or 0)
        tokens_saved = int(metrics.get("unified_tokens_saved") or max(raw_tokens - context_tokens, 0))
        if raw_tokens <= 0 and context_tokens > 0:
            raw_tokens = context_tokens + tokens_saved
        reduction = metrics.get("unified_savings_pct", metrics.get("savings_pct", 0.0))
        try:
            reduction = float(reduction)
        except (TypeError, ValueError):
            reduction = (tokens_saved / raw_tokens * 100.0) if raw_tokens else 0.0

        return {
            "status": "PASS" if ctx_file.exists() else "WARN",
            "project_root": str(project_resolved),
            "context_file": str(ctx_file),
            "files_scanned": file_count,
            "symbols_extracted": symbol_count,
            "normal_tokens": raw_tokens,
            "bbc_tokens": context_tokens,
            "tokens_avoided": tokens_saved,
            "reduction_pct": round(reduction, 2),
            "context_fresh": bool(ctx.get("context_fresh", False)),
            "constraint_status": ctx.get("constraint_status", ctx.get("recipe", {}).get("constraint_status", "unknown")),
        }

    def integrations(self, project_path: str = ".", json_output: bool = False, check: bool = False):
        """Show detected AI coding integrations and BBC support posture."""
        project_root = Path(project_path).resolve()
        try:
            from bbc_core.ide_auto_config import IDEAutoConfigurator

            configurator = IDEAutoConfigurator()
            active_ide = configurator.detect_active_ide()
            detected = configurator.detect_active_integrations(project_root)
        except Exception as e:
            active_ide = None
            detected = []
            detect_error = str(e)
        else:
            detect_error = None

        detected_ids = {item.get("id") for item in detected}
        known = [
            ("vscode", "VS Code / GitHub Copilot", "adapter-backed"),
            ("cursor", "Cursor", "adapter-backed"),
            ("windsurf", "Windsurf", "instruction-backed"),
            ("antigravity", "Antigravity-style rules", "instruction-backed"),
            ("cline", "Cline / Kilo", "adapter-backed"),
            ("jetbrains", "JetBrains", "adapter-backed"),
            ("zed", "Zed", "adapter-backed"),
            ("theia", "Eclipse Theia", "adapter-backed"),
            ("trae", "Trae", "instruction-backed"),
        ]
        integrations = []
        for ident, label, support in known:
            integrations.append({
                "id": ident,
                "label": label,
                "support": support,
                "detected": ident in detected_ids or active_ide == ident,
            })

        report = {
            "status": "PASS" if not check or any(item["detected"] for item in integrations) else "WARN",
            "project_root": str(project_root),
            "active_ide": active_ide or "unknown",
            "detect_error": detect_error,
            "detected_count": sum(1 for item in integrations if item["detected"]),
            "integrations": integrations,
        }

        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if report["status"] == "PASS" else 1

        print("\n" + "=" * 60)
        print(" BBC INTEGRATIONS")
        print("=" * 60)
        print(f"Project:    {report['project_root']}")
        print(f"Active IDE: {report['active_ide']}")
        for item in integrations:
            mark = "OK" if item["detected"] else "SKIP"
            print(f"[{mark:4}] {item['label']}: {item['support']}")
        if detect_error:
            print(f"[WARN] detection error: {detect_error}")
        print("=" * 60)
        return 0 if report["status"] == "PASS" else 1

    def preview(self, project_path: str = ".", json_output: bool = False):
        """Dry-run what BBC init would do, without writing files."""
        project_root = Path(project_path).resolve()
        integration_report = self._integration_report_for_preview(project_root)
        bbc_dir = project_root / ".bbc"
        ctx_file = bbc_dir / "bbc_context.json"
        actions = [
            {"action": "analyze", "target": ".bbc/bbc_context.json", "will_write": True},
            {"action": "update-gitignore", "target": ".gitignore", "will_write": True},
            {"action": "write-central-rules", "target": ".bbc/BBC_INSTRUCTIONS.md", "will_write": True},
        ]
        for item in integration_report:
            actions.append({
                "action": "inject",
                "target": item.get("rel_path", item.get("id", "unknown")),
                "label": item.get("label", item.get("id", "unknown")),
                "will_write": True,
            })

        skipped = []
        if not integration_report:
            skipped.append("No active IDE/extension surface detected; BBC will keep rules inside .bbc only.")
        skipped.extend([
            "BBC will not create unused IDE folders.",
            "BBC will not push anything to GitHub.",
            "BBC will not upload source code to a BBC server.",
            "BBC will not touch project source files during init.",
        ])

        report = {
            "status": "PASS",
            "project_root": str(project_root),
            "context_exists": ctx_file.exists(),
            "actions": actions,
            "skipped": skipped,
        }

        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0

        print("\n" + "=" * 60)
        print(" BBC PREVIEW")
        print("=" * 60)
        print(f"Project: {project_root}")
        for action in actions:
            label = f" ({action['label']})" if action.get("label") else ""
            print(f"[WILL] {action['action']}: {action['target']}{label}")
        for item in skipped:
            print(f"[SKIP] {item}")
        print("=" * 60)
        return 0

    def _integration_report_for_preview(self, project_root: Path):
        try:
            from bbc_core.ide_auto_config import IDEAutoConfigurator

            return IDEAutoConfigurator().detect_active_integrations(project_root)
        except Exception:
            return []

    def rule_health(self, project_path: str = ".", json_output: bool = False):
        """Check central and injected BBC rule files for required invariants."""
        project_root = Path(project_path).resolve()
        candidate_paths = [
            project_root / ".bbc" / "BBC_INSTRUCTIONS.md",
            project_root / ".bbc" / "bbc_rules.md",
        ]
        manifest = project_root / ".bbc" / "manifest" / "injected_files.json"
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                for entry in data.get("files", []):
                    path = Path(entry.get("path", ""))
                    if path.exists():
                        candidate_paths.append(path)
            except Exception:
                pass

        files = []
        for path in candidate_paths:
            rel = path.relative_to(project_root).as_posix() if path.exists() and path.is_relative_to(project_root) else str(path)
            if not path.exists():
                files.append({"path": rel, "exists": False, "ok": False, "missing": list(BBC_RULE_INVARIANTS)})
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            missing = []
            for name, needles in BBC_RULE_INVARIANTS.items():
                if not any(needle in text for needle in needles):
                    missing.append(name)
            files.append({"path": rel, "exists": True, "ok": not missing, "missing": missing})

        required_files = [item for item in files if item["path"].endswith("BBC_INSTRUCTIONS.md") or item["path"].endswith("bbc_rules.md")]
        existing_required = [item for item in required_files if item["exists"]]
        if existing_required:
            status = "PASS" if all(item["ok"] for item in existing_required) else "FAIL"
        else:
            status = "WARN"
        report = {"status": status, "project_root": str(project_root), "files": files}

        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if status in {"PASS", "WARN"} else 1

        print("\n" + "=" * 60)
        print(" BBC RULE HEALTH")
        print("=" * 60)
        for item in files:
            mark = "OK" if item["ok"] else "FAIL"
            missing = f" missing={','.join(item['missing'])}" if item["missing"] else ""
            print(f"[{mark:4}] {item['path']}{missing}")
        print(f"Status: {status}")
        print("=" * 60)
        return 0 if status in {"PASS", "WARN"} else 1

    def security_check(self, project_path: str = ".", json_output: bool = False):
        """Scan for publish blockers, personal paths, and obvious secret markers."""
        from bbc_core.project_hygiene import publish_check_report

        project_root = Path(project_path).resolve()
        publish_report = publish_check_report(str(project_root))
        secret_findings = self._scan_secret_markers(project_root)
        status = "PASS" if publish_report["status"] == "PASS" and not secret_findings else "FAIL"
        report = {
            "status": status,
            "project_root": str(project_root),
            "publish_check": publish_report,
            "secret_findings": secret_findings,
        }

        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if status in {"PASS", "WARN"} else 1

        print("\n" + "=" * 60)
        print(" BBC SECURITY CHECK")
        print("=" * 60)
        print(f"Publish hygiene: {publish_report['status']}")
        for marker in publish_report.get("personal_path_markers", []):
            print(f"[FAIL] personal path in {marker['file']} ({marker['marker']})")
        for finding in secret_findings:
            print(f"[FAIL] {finding['kind']} marker in {finding['file']}")
        if status == "PASS":
            print("[OK  ] No publish blockers or obvious secret markers found.")
        print("=" * 60)
        return 0 if status in {"PASS", "WARN"} else 1

    def _scan_secret_markers(self, project_root: Path, limit: int = 25):
        findings = []
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in SECURITY_SKIP_DIRS and not d.startswith(".pytest-tmp")]
            for file_name in files:
                path = Path(root) / file_name
                if path.suffix.lower() not in SECURITY_SCAN_EXTENSIONS and path.name != ".env":
                    continue
                try:
                    rel = path.relative_to(project_root).as_posix()
                    text = path.read_text(encoding="utf-8", errors="ignore").lower()
                except Exception:
                    continue
                for kind, pattern in SECRET_PATTERNS.items():
                    if pattern.search(text):
                        if "example" in rel.lower() or "placeholder" in text:
                            continue
                        findings.append({"file": rel, "kind": kind})
                        break
                if len(findings) >= limit:
                    return findings
        return findings

    def readiness(self, project_path: str = ".", json_output: bool = False):
        """Combine doctor, benchmark, publish, security, and rule-health status."""
        from bbc_core.project_hygiene import doctor_report, publish_check_report

        project_root = Path(project_path).resolve()
        doctor = doctor_report(str(project_root))
        benchmark = self._benchmark_report(str(project_root))
        publish = publish_check_report(str(project_root))
        secret_findings = self._scan_secret_markers(project_root)
        rule_report = self._rule_health_report(project_root)

        checks = [
            {"name": "doctor", "status": doctor["status"]},
            {"name": "benchmark", "status": benchmark["status"]},
            {"name": "publish-check", "status": publish["status"]},
            {"name": "security-check", "status": "PASS" if not secret_findings else "FAIL"},
            {"name": "rule-health", "status": rule_report["status"]},
        ]
        status = "PASS" if all(item["status"] == "PASS" for item in checks) else "WARN"
        if any(item["status"] == "FAIL" for item in checks):
            status = "FAIL"
        report = {
            "status": status,
            "project_root": str(project_root),
            "checks": checks,
            "benchmark": benchmark,
            "secret_findings": secret_findings,
        }

        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0 if status in {"PASS", "WARN"} else 1

        print("\n" + "=" * 60)
        print(" BBC READINESS")
        print("=" * 60)
        for check in checks:
            mark = "OK" if check["status"] == "PASS" else check["status"]
            print(f"[{mark:4}] {check['name']}")
        if benchmark.get("status") == "PASS":
            print(f"Tokens avoided: {benchmark['tokens_avoided']:,} ({benchmark['reduction_pct']:.1f}%)")
        print(f"Status: {status}")
        print("=" * 60)
        return 0 if status in {"PASS", "WARN"} else 1

    def _rule_health_report(self, project_root: Path):
        central = project_root / ".bbc" / "BBC_INSTRUCTIONS.md"
        rules = project_root / ".bbc" / "bbc_rules.md"
        files = []
        for path in [central, rules]:
            if not path.exists():
                files.append({"path": path.name, "ok": False})
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            ok = all(any(needle in text for needle in needles) for needles in BBC_RULE_INVARIANTS.values())
            files.append({"path": path.name, "ok": ok})
        existing = [item for item in files if (project_root / ".bbc" / item["path"]).exists()]
        if existing:
            status = "PASS" if all(item["ok"] for item in existing) else "FAIL"
        else:
            status = "WARN"
        return {"status": status, "files": files}

    def mode(self, project_path: str = ".", value: str = None, json_output: bool = False):
        """Read or set BBC context mode metadata."""
        project_root = Path(project_path).resolve()
        config_path = project_root / ".bbc" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        except Exception:
            config = {}

        if value:
            if value not in {"speed", "quality", "balanced"}:
                print("[BBC] Mode must be one of: speed, quality, balanced")
                return 1
            config["context_mode"] = value
            config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

        current = config.get("context_mode", "balanced")
        report = {
            "status": "PASS",
            "project_root": str(project_root),
            "mode": current,
            "notes": {
                "speed": "Prefer smaller packs and faster checks where safe.",
                "quality": "Prefer stronger evidence and guardrails for critical work.",
                "balanced": "Default BBC behavior.",
            }[current],
        }
        if json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"BBC mode: {current}")
            print(report["notes"])
        return 0

    def self_test(self, keep_temp: bool = False):
        """Run a local BBC health check against a temporary project."""
        print("\nBBC SELF-TEST")
        temp_dir = Path(tempfile.mkdtemp(prefix="bbc-self-test-"))
        checks = []

        def record(name: str, ok: bool, detail: str = ""):
            checks.append((name, ok, detail))
            mark = "OK" if ok else "FAIL"
            suffix = f" - {detail}" if detail else ""
            print(f"[{mark}] {name}{suffix}")

        try:
            record("Python runtime", sys.version_info >= (3, 8), sys.version.split()[0])

            try:
                import bbc_core.agent_adapter  # noqa: F401
                import bbc_core.native_adapter  # noqa: F401
                import bbc_core.verifier  # noqa: F401
                record("Required imports", True)
            except Exception as e:
                record("Required imports", False, str(e))

            (temp_dir / "sample.py").write_text(
                "def hello(name):\n    return f'hello {name}'\n\nclass Greeter:\n    pass\n",
                encoding="utf-8",
            )
            (temp_dir / ".gitignore").write_text(".bbc/\n", encoding="utf-8")

            analyze_ok = self.run_command(["analyze", str(temp_dir), "--silent"]) == 0
            ctx_file = temp_dir / ".bbc" / "bbc_context.json"
            record("Temporary project analysis", analyze_ok and ctx_file.exists())

            verify_ok = False
            if ctx_file.exists():
                verify_ok = self.run_command(["verify", str(ctx_file)]) == 0
            record("Context verification", verify_ok)

            inject_ok = False
            if ctx_file.exists():
                inject_ok = self.run_command(["inject", str(temp_dir), "--silent", "--no-optimize"]) == 0
            instructions = temp_dir / ".bbc" / "BBC_INSTRUCTIONS.md"
            invariant_ok = False
            if instructions.exists():
                text = instructions.read_text(encoding="utf-8", errors="ignore").lower()
                invariant_ok = "reuse-first" in text and "hallucination" in text and "sealed" in text
            record("Adapter invariant rules", inject_ok and invariant_ok)

            publish_ok = self.run_command(["publish-check", str(temp_dir)]) == 0
            record("Publish hygiene", publish_ok)

            passed = all(ok for _, ok, _ in checks)
            print(f"\nResult: {'PASS' if passed else 'FAIL'}")
            if keep_temp:
                print(f"Temp project kept at: {temp_dir}")
            return 0 if passed else 1
        finally:
            if not keep_temp:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def start(self, project_path: str = ".", background: bool = False, force: bool = False):
        """Start BBC - The Full v8.6 Pipeline"""
        project_resolved = str(Path(project_path).resolve())

        if background:
            daemon_script = self.script_dir / "bbc_daemon.py"
            creation_flags = 0
            if os.name == 'nt':
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW

            proc = subprocess.Popen(
                [sys.executable, str(daemon_script), "start", project_resolved],
                creationflags=creation_flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print(f"[BBC] Daemon started (PID: {proc.pid})")
            return

        print(f"[BBC] Initializing Master v8.6 Pipeline...")

        # 1. Verify Structure (use correct .bbc/ path)
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if Path(ctx_file).exists():
            self.run_command(["verify", ctx_file])

        # 2. Analyze & Inject
        success = auto_start_bbc(force_restart=force, project_path=project_path, start_monitoring=False)

        if success:
            print(f"[BBC] Injecting Adaptive Mode Intelligence...")
            if force:
                self.run_command(["analyze", project_resolved])
                self.run_command(["inject", project_resolved, "--auto-analyze", "--silent", "--force"])
            else:
                self.run_command(["inject", project_resolved, "--auto-analyze", "--silent"])
            print(f"[BBC] System Active. Zero-Hallucination Guard Engaged.")
            
            # Otomatik daemon başlat (Arka plan servisi)
            if not background:
                print(f"[BBC] Starting Real-time Daemon in background...")
                daemon_script = self.script_dir / "bbc_daemon.py"
                creation_flags = 0
                if os.name == 'nt':
                    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
                try:
                    proc = subprocess.Popen(
                        [sys.executable, str(daemon_script), "start", project_resolved],
                        creationflags=creation_flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    print(f"[BBC] Daemon started (PID: {proc.pid}) - Real-time monitoring active.")
                except Exception as e:
                    print(f"[WARN] Could not start daemon automatically: {e}")
            
            # Start IDE terminal watch (foreground) — shows HMPU report after each AI operation
            self._watch_and_report(project_resolved)
        else:
            print(f"[BBC] Initialization failed.")
            sys.exit(1)

    def _watch_and_report(self, project_path: str):
        """Watch .bbc/last_activity.json and print HMPU report after each AI operation in IDE terminal"""
        activity_file = Path(project_path) / ".bbc" / "last_activity.json"
        print(f"[BBC] IDE Terminal Watch active. Monitoring AI operations...")
        print(f"[BBC] Press Ctrl+C to stop watching.\n")
        
        last_epoch = 0.0
        quiet_since = None  # timestamp when activity stopped
        DEBOUNCE_SECONDS = 3.0  # wait this long after last change before printing report
        
        try:
            while True:
                try:
                    if activity_file.exists():
                        with open(activity_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        current_epoch = data.get("epoch", 0.0)
                        
                        if current_epoch > last_epoch:
                            last_epoch = current_epoch
                            quiet_since = time.time()
                    
                    # If we have pending activity and enough quiet time passed, print report
                    if quiet_since and (time.time() - quiet_since) >= DEBOUNCE_SECONDS:
                        quiet_since = None
                        # Re-read activity info for display
                        try:
                            with open(activity_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            changed_file = data.get("file", "")
                            print(f"\n[BBC] Activity detected: {changed_file}")
                        except Exception:
                            pass
                        
                        # Print HMPU transaction report
                        try:
                            sys.argv = ["run_bbc", "analyze", project_path]
                            from run_bbc import print_transaction_report
                            print_transaction_report()
                        except Exception as e:
                            print(f"[BBC] Report error: {e}")
                
                except (json.JSONDecodeError, PermissionError):
                    pass
                
                time.sleep(1.0)
        except KeyboardInterrupt:
            print(f"\n[BBC] Watch stopped.")

    def watch(self, project_path: str = "."):
        """Watch mode - monitor AI operations and print HMPU reports in IDE terminal"""
        project_resolved = str(Path(project_path).resolve())
        ctx_file = Path(project_resolved) / ".bbc" / "bbc_context.json"
        if not ctx_file.exists():
            print(f"[BBC] Project not initialized. Run 'bbc start' first.")
            sys.exit(1)
        
        # Print initial report
        try:
            sys.argv = ["run_bbc", "analyze", project_resolved]
            from run_bbc import print_transaction_report
            print_transaction_report()
        except Exception:
            pass
        
        self._watch_and_report(project_resolved)

    def stop(self, project_path: str = "."):
        project_resolved = str(Path(project_path).resolve())
        from bbc_daemon import BBCDaemon
        daemon = BBCDaemon(project_root=project_resolved)
        if daemon._is_running():
            daemon.stop()
        else:
            stop_bbc_auto()
        print(f"[BBC] Stopped")

    def purge(self, path=".", force=False):
        """Complete system purge"""
        cmd = ["purge", str(Path(path).resolve())]
        if force: cmd.append("--force")
        self.run_command(cmd)

    def install(self, project_path: str = ".", force: bool = False):
        """One-command BBC install: pip install deps + analyze + inject + start"""
        print(f"[BBC] One-Command Install starting...")
        
        # 1. Install dependencies
        req_file = self.script_dir / "requirements.txt"
        if req_file.exists():
            print(f"[BBC] Step 1/2: Installing dependencies...")
            result = subprocess.call(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"]
            )
            if result != 0:
                print(f"[BBC] Warning: Some dependencies may have failed to install.")
            else:
                print(f"[BBC] Step 1/2: Dependencies installed.")
        else:
            print(f"[BBC] Step 1/2: No requirements.txt found, skipping.")
        
        # 2. Run full start pipeline
        print(f"[BBC] Step 2/2: Starting BBC...")
        self.start(project_path, force=force)

    def serve(self, port=3333):
        """Start HTTP API Server"""
        print(f"[BBC] Starting API Server on port {port}...")
        os.environ["BBC_API_PORT"] = str(port)
        try:
            from bbc_core.http_server import app
            import uvicorn
        except ImportError as e:
            print(f"[BBC] Server dependency missing: {e}")
            print("[BBC] Run 'pip install -r requirements.txt' in the BBC repo, then retry 'bbc serve'.")
            sys.exit(1)
        uvicorn.run(app, host="127.0.0.1", port=port)

def main():
    parser = argparse.ArgumentParser(description="BBC Master CLI - v8.6 STABLE", prog="bbc")
    parser.add_argument("--version", action="version", version=f"BBC {BBC_VERSION}")
    parser.add_argument("--enforcement", choices=["strict", "balanced", "relaxed"], default=None,
                        help="Override enforcement level (default: read from context or strict)")
    parser.add_argument("--fail-policy", choices=["fail_closed", "fail_open"], default=None,
                        help="Override fail policy (default: read from context or fail_closed)")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Init
    init_parser = subparsers.add_parser("init", help="Initialize BBC without starting watch/daemon")
    init_parser.add_argument("path", nargs="?", default=".", help="Project path")
    init_parser.add_argument("--force", "-f", action="store_true", help="Force fresh analyze/inject")
    init_parser.add_argument("--no-inject", action="store_true", help="Analyze and doctor only")

    # Self-test
    self_test_parser = subparsers.add_parser("self-test", help="Run BBC's local installation health check")
    self_test_parser.add_argument("--keep-temp", action="store_true", help="Keep the temporary self-test project")

    # Benchmark
    benchmark_parser = subparsers.add_parser("benchmark", help="Show token reduction and context readiness metrics")
    benchmark_parser.add_argument("path", nargs="?", default=".", help="Project path")
    benchmark_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Integrations
    integrations_parser = subparsers.add_parser("integrations", help="Show detected AI coding integrations")
    integrations_parser.add_argument("path", nargs="?", default=".", help="Project path")
    integrations_parser.add_argument("--json", action="store_true", help="Output JSON")
    integrations_parser.add_argument("--check", action="store_true", help="Return non-zero if no integration is detected")

    # Preview
    preview_parser = subparsers.add_parser("preview", help="Preview what BBC init would write without changing files")
    preview_parser.add_argument("path", nargs="?", default=".", help="Project path")
    preview_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Readiness
    readiness_parser = subparsers.add_parser("readiness", help="Combined BBC readiness report")
    readiness_parser.add_argument("path", nargs="?", default=".", help="Project path")
    readiness_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Security Check
    security_parser = subparsers.add_parser("security-check", help="Scan publish blockers and obvious secret markers")
    security_parser.add_argument("path", nargs="?", default=".", help="Project path")
    security_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Rule Health
    rule_health_parser = subparsers.add_parser("rule-health", help="Check BBC injected rule invariants")
    rule_health_parser.add_argument("path", nargs="?", default=".", help="Project path")
    rule_health_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Mode
    mode_parser = subparsers.add_parser("mode", help="Read or set BBC context mode metadata")
    mode_parser.add_argument("value", nargs="?", choices=["speed", "quality", "balanced"], help="Mode to set")
    mode_parser.add_argument("--path", default=".", help="Project path")
    mode_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Start
    start_parser = subparsers.add_parser("start", help="Full Verify + Analyze + Inject")
    start_parser.add_argument("path", nargs="?", default=".", help="Project path")
    start_parser.add_argument("--background", "-b", action="store_true", help="Run in background")
    start_parser.add_argument("--force", "-f", action="store_true", help="Force refresh")

    # Analyze (Direct)
    analyze_parser = subparsers.add_parser("analyze", help="Deep Project Scan")
    analyze_parser.add_argument("path", nargs="?", default=".", help="Project path")
    analyze_parser.add_argument("--incremental", action="store_true",
                               help="Only re-analyze files changed since last run")

    # Verify
    verify_parser = subparsers.add_parser("verify", help="Check Structural Integrity")
    verify_parser.add_argument("path", nargs="?", default=".", help="Project path")
    verify_parser.add_argument("--changed-only", action="store_true",
                               help="Only verify files that changed since last seal")

    # Serve
    serve_parser = subparsers.add_parser("serve", help="Start API Server")
    serve_parser.add_argument("--port", "-p", type=int, default=3333, help="Port (default: 3333)")

    # Audit
    audit_parser = subparsers.add_parser("audit", help="Audit BBC Traces")
    audit_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # Doctor
    doctor_parser = subparsers.add_parser("doctor", help="Check BBC environment, context, IDE signals, and Git hygiene")
    doctor_parser.add_argument("path", nargs="?", default=".", help="Project path")
    doctor_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Publish Check
    publish_parser = subparsers.add_parser("publish-check", help="Check target project for BBC traces before GitHub publish")
    publish_parser.add_argument("path", nargs="?", default=".", help="Project path")
    publish_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Runtime Clean
    clean_parser = subparsers.add_parser("clean", help="Clean BBC runtime logs/cache with retention limits")
    clean_parser.add_argument("path", nargs="?", default=".", help="Project path")
    clean_parser.add_argument("--older-than-days", type=int, default=14, help="Remove runtime files older than N days")
    clean_parser.add_argument("--max-mb", type=int, default=50, help="Keep .bbc runtime footprint below this size")
    clean_parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")
    clean_parser.add_argument("--json", action="store_true", help="Output JSON")

    # Purge
    purge_parser = subparsers.add_parser("purge", help="Complete BBC Removal")
    purge_parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")
    purge_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # Menu (Interactive)
    menu_parser = subparsers.add_parser("menu", help="Interactive BBC Menu")
    menu_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # Install (One-command setup)
    install_parser = subparsers.add_parser("install", help="One-command install: deps + analyze + inject + start")
    install_parser.add_argument("path", nargs="?", default=".", help="Project path")
    install_parser.add_argument("--force", "-f", action="store_true", help="Force fresh install")

    # Watch (IDE Terminal Monitor)
    watch_parser = subparsers.add_parser("watch", help="Watch AI operations and show HMPU reports in IDE terminal")
    watch_parser.add_argument("path", nargs="?", default=".", help="Project path")

    stop_parser = subparsers.add_parser("stop", help="Stop BBC Daemon")
    stop_parser.add_argument("path", nargs="?", default=".", help="Project path")

    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # Check (Hallucination Guard)
    check_parser = subparsers.add_parser("check", help="Check AI-generated code against sealed BBC context")
    check_parser.add_argument("file", help="Path to file containing AI-generated code to check")
    check_parser.add_argument("--path", default=".", help="Project path (default: current directory)")
    check_parser.add_argument("--strict", action="store_true", default=True, help="Strict mode: flag all unknown symbols")
    check_parser.add_argument("--relaxed", action="store_true", help="Relaxed mode: only flag speculative language")

    # Impact (Semantic Impact Analysis)
    impact_parser = subparsers.add_parser("impact", help="Analyze semantic impact of a file change (BBC Mathematics)")
    impact_parser.add_argument("file", help="Path to the changed file")
    impact_parser.add_argument("--path", default=".", help="Project path (default: current directory)")
    impact_parser.add_argument("--symbols", nargs="*", default=None, help="Changed symbol names (optional)")
    impact_parser.add_argument("--op", choices=["Refactor", "Patch", "Feature"], default="Patch",
                               help="Operation type (default: Patch)")

    # Patch (Auto Patcher)
    patch_parser = subparsers.add_parser("patch", help="Detect and fix code issues automatically (BBC Mathematics)")
    patch_parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")
    patch_parser.add_argument("--apply", action="store_true", help="Apply safe patches (default: dry-run only)")

    # Inject (Agent Instruction Injection)
    inject_parser = subparsers.add_parser("inject", help="Inject BBC instructions into AI agent config files")
    inject_parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")
    inject_parser.add_argument("--no-optimize", action="store_true", help="Disable agent-specific optimized context injection")

    # Hooks (Git Hook Generator)
    hooks_parser = subparsers.add_parser("hooks", help="Install/remove BBC git hooks for team automation")
    hooks_parser.add_argument("path", nargs="?", default=".", help="Project path")
    hooks_parser.add_argument("--remove", action="store_true", help="Remove BBC hooks")

    # Pack (Semantic Packer)
    pack_parser = subparsers.add_parser("pack", help="Semantically compress context for minimal token usage")
    pack_parser.add_argument("--path", default=".", help="Project path (default: current directory)")
    pack_parser.add_argument("--aggressive", action="store_true", help="Deeper compression, removes dep graph")
    pack_parser.add_argument("--out", default=None, help="Output path for packed context")
    pack_parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")

    # Compile (Task-Aware Context Compiler)
    compile_parser = subparsers.add_parser("compile", help="Compile task-aware context (bugfix/feature/refactor/review)")
    compile_parser.add_argument("--task", required=True,
                                choices=["bugfix", "feature", "refactor", "review"],
                                help="Task type")
    compile_parser.add_argument("--file", default=None, help="Target file (relative path)")
    compile_parser.add_argument("--symbols", nargs="*", default=None, help="Target symbol names")
    compile_parser.add_argument("--path", default=".", help="Project path (default: current directory)")
    compile_parser.add_argument("--out", default=None, help="Output path for compiled context")
    compile_parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")

    # Telemetry (Feedback Dashboard)
    telemetry_parser = subparsers.add_parser("telemetry", help="Show BBC performance telemetry dashboard")
    telemetry_parser.add_argument("path", nargs="?", default=".", help="Project path")
    telemetry_parser.add_argument("--json", action="store_true", help="Output raw JSON")
    telemetry_parser.add_argument("--limit", type=int, default=10, help="Number of recent commands")

    # Usage (Exact Token Analyzer)
    usage_parser = subparsers.add_parser("usage", help="Show IDE token usage when available, otherwise fallback status")
    usage_parser.add_argument("path", nargs="?", default=".", help="Project path")

    # Episodic Memory
    remember_parser = subparsers.add_parser("remember", help="Save user preference or decision to episodic memory")
    remember_parser.add_argument("topic", help="Topic or key")
    remember_parser.add_argument("content", help="Content to remember")
    remember_parser.add_argument("--path", default=".", help="Project path")
    remember_parser.add_argument("--force", action="store_true", help="Overwrite an existing memory for this topic")

    recall_parser = subparsers.add_parser("recall", help="Recall user preference or decision from episodic memory")
    recall_parser.add_argument("query", help="Query string to search for")
    recall_parser.add_argument("--path", default=".", help="Project path")

    args = parser.parse_args()
    cli = BBCCLI()

    # --- Telemetry: start timer for all commands ---
    _tele_start = time.time()
    _tele_command = args.command or "help"

    if args.command == "init":
        sys.exit(cli.init(args.path, force=args.force, no_inject=args.no_inject))
    elif args.command == "self-test":
        sys.exit(cli.self_test(keep_temp=args.keep_temp))
    elif args.command == "benchmark":
        sys.exit(cli.benchmark(args.path, json_output=args.json))
    elif args.command == "integrations":
        sys.exit(cli.integrations(args.path, json_output=args.json, check=args.check))
    elif args.command == "preview":
        sys.exit(cli.preview(args.path, json_output=args.json))
    elif args.command == "readiness":
        sys.exit(cli.readiness(args.path, json_output=args.json))
    elif args.command == "security-check":
        sys.exit(cli.security_check(args.path, json_output=args.json))
    elif args.command == "rule-health":
        sys.exit(cli.rule_health(args.path, json_output=args.json))
    elif args.command == "mode":
        sys.exit(cli.mode(args.path, value=args.value, json_output=args.json))
    elif args.command == "start":
        cli.start(args.path, args.background, args.force)
    elif args.command == "analyze":
        cmd = ["analyze", args.path]
        if getattr(args, "incremental", False):
            cmd.append("--incremental")
        cli.run_command(cmd)
    elif args.command == "usage":
        cli.run_command(["usage", "--path", args.path])
    elif args.command == "remember":
        cmd = ["remember", args.topic, args.content, "--path", args.path]
        if getattr(args, "force", False):
            cmd.append("--force")
        cli.run_command(cmd)
    elif args.command == "recall":
        cli.run_command(["recall", args.query, "--path", args.path])
    elif args.command == "verify":
        project_resolved = str(Path(args.path).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if Path(ctx_file).exists():
            # --- Freshness gate ---
            from bbc_core.cli import _is_context_stale
            stale = _is_context_stale(project_resolved, ctx_file)
            if stale:
                _update_context_freshness(ctx_file, False)
            # --- Read policy from context (with CLI overrides) ---
            import json as _json
            with open(ctx_file, "r", encoding="utf-8") as _f:
                _ctx = _json.load(_f)
            fp = getattr(args, "fail_policy", None) or _ctx.get("fail_policy", "fail_closed")
            enf = getattr(args, "enforcement", None) or _ctx.get("enforcement_level", "strict")
            # --- Apply CLI overrides to context if provided ---
            _dirty = False
            if getattr(args, "enforcement", None) and args.enforcement != _ctx.get("enforcement_level"):
                _ctx["enforcement_level"] = args.enforcement
                _dirty = True
            if getattr(args, "fail_policy", None) and args.fail_policy != _ctx.get("fail_policy"):
                _ctx["fail_policy"] = args.fail_policy
                _dirty = True
            if _dirty:
                with open(ctx_file, "w", encoding="utf-8") as _f:
                    _json.dump(_ctx, _f, indent=2, ensure_ascii=False)
            # --- Freshness warning/block ---
            if stale:
                print(f"[BBC] Context freshness: STALE")
                if fp == "fail_closed":
                    print(f"[BBC] Fail policy: fail_closed — run 'bbc analyze {args.path}' to refresh context before proceeding.")
                else:
                    print(f"[BBC WARNING] Operating with stale context (fail_open mode).")
            else:
                print(f"[BBC] Context freshness: FRESH")
            print(f"[BBC] Enforcement: {enf} | Fail policy: {fp}")
            verify_cmd = ["verify", ctx_file]
            if getattr(args, "changed_only", False):
                verify_cmd.append("--changed-only")
            cli.run_command(verify_cmd)
        else:
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc start {args.path}' first to generate the context.")
    elif args.command == "check":
        project_resolved = str(Path(getattr(args, 'path', '.')).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if Path(ctx_file).exists():
            candidate_file = Path(args.file)
            if not candidate_file.is_absolute():
                candidate_file = Path(project_resolved) / candidate_file
            cmd = ["check", str(candidate_file.resolve()), "--context", ctx_file]
            if getattr(args, "relaxed", False):
                cmd.append("--relaxed")
            elif getattr(args, "strict", False):
                cmd.append("--strict")
            cli.run_command(cmd)
        else:
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc start {args.path}' first to generate the context.")
    elif args.command == "serve":
        cli.serve(args.port)
    elif args.command == "audit":
        cli.run_command(["audit", args.path])
    elif args.command == "doctor":
        cmd = ["doctor", args.path]
        if getattr(args, "json", False):
            cmd.append("--json")
        cli.run_command(cmd)
    elif args.command == "publish-check":
        cmd = ["publish-check", args.path]
        if getattr(args, "json", False):
            cmd.append("--json")
        cli.run_command(cmd)
    elif args.command == "clean":
        cmd = [
            "clean",
            args.path,
            "--older-than-days",
            str(args.older_than_days),
            "--max-mb",
            str(args.max_mb),
        ]
        if getattr(args, "dry_run", False):
            cmd.append("--dry-run")
        if getattr(args, "json", False):
            cmd.append("--json")
        cli.run_command(cmd)
    elif args.command == "purge":
        cli.purge(args.path, args.force)
    elif args.command == "menu":
        from bbc_core.global_menu import main as menu_main
        menu_main(str(Path(args.path).resolve()), loop=True)
    elif args.command == "watch":
        cli.watch(args.path)
    elif args.command == "install":
        cli.install(args.path, args.force)
    elif args.command == "inject":
        project_resolved = str(Path(args.path).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if Path(ctx_file).exists():
            from bbc_core.agent_adapter import inject_to_project
            created = inject_to_project(
                ctx_file,
                project_resolved,
                optimize=not getattr(args, "no_optimize", False),
                active_command="inject",
            )
            print(f"\n[BBC] Injection complete — {len(created)} target(s):")
            for label, path in created.items():
                print(f"  [{label}] {path}")
            _print_transaction_report(project_resolved, "inject")
        else:
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc analyze {args.path}' first to generate the context.")
    elif args.command == "stop":
        cli.stop(args.path)
    elif args.command == "status":
        project_resolved = str(Path(args.path).resolve())
        daemon = __import__("bbc_daemon").BBCDaemon(project_root=project_resolved)
        daemon_active = daemon._is_running()
        
        print("\n" + "="*40)
        print(" BBC v8.6 - System Status ".center(40, "="))
        print("="*40)
        import json

        ctx_path = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if os.path.exists(ctx_path):
            print(f"[X] Context Lock:   SEALED (ACTIVE)")
        else:
            print(f"[ ] Context Lock:   MISSING (VULNERABLE)")
            
        if daemon_active:
            print(f"[~] Daemon Status:  RUNNING (Dynamic)")
            try:
                if daemon.config_file.exists():
                    with open(daemon.config_file, "r") as f:
                        cfg = json.load(f)
                    print(f"    - Monitoring:   {cfg.get('project_path', 'Unknown')}")
                    print(f"    - Started:      {cfg.get('start_time', 'Unknown')}")
            except Exception:
                pass
        else:
            print(f"[!] Daemon Status:  STOPPED (Static Mode)")
            print("    Run 'bbc start' to enable live defense.")
            
        print("="*40 + "\n")
    elif args.command == "telemetry":
        telemetry_cmd = ["telemetry", args.path]
        if getattr(args, "json", False):
            telemetry_cmd.append("--json")
        if getattr(args, "limit", 10) != 10:
            telemetry_cmd.extend(["--limit", str(args.limit)])
        cli.run_command(telemetry_cmd)
    elif args.command == "pack":
        project_resolved = str(Path(getattr(args, 'path', '.')).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if not Path(ctx_file).exists():
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc analyze' first.")
        else:
            pack_cmd = ["pack", "--context", ctx_file]
            if getattr(args, "aggressive", False):
                pack_cmd.append("--aggressive")
            if getattr(args, "out", None):
                pack_cmd.extend(["--out", args.out])
            if getattr(args, "json", False):
                pack_cmd.append("--json")
            cli.run_command(pack_cmd)
    elif args.command == "compile":
        project_resolved = str(Path(getattr(args, 'path', '.')).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if not Path(ctx_file).exists():
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc analyze' first.")
        else:
            compile_cmd = ["compile", "--task", args.task]
            if getattr(args, "file", None):
                compile_cmd.extend(["--file", args.file])
            if getattr(args, "symbols", None):
                compile_cmd.extend(["--symbols"] + args.symbols)
            compile_cmd.extend(["--context", ctx_file])
            if getattr(args, "out", None):
                compile_cmd.extend(["--out", args.out])
            if getattr(args, "json", False):
                compile_cmd.append("--json")
            cli.run_command(compile_cmd)
    elif args.command == "impact":
        project_resolved = str(Path(getattr(args, 'path', '.')).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if not Path(ctx_file).exists():
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc analyze' first.")
        else:
            from bbc_core.impact_analyzer import ImpactAnalyzer
            analyzer = ImpactAnalyzer(ctx_file)
            report = analyzer.analyze_impact(args.file, changed_symbols=args.symbols, op_type=args.op)
            aura = report["aura_impact"]
            print(f"\n{'='*60}")
            print(f" {report['verdict_icon']} BBC SEMANTIC IMPACT ANALYSIS")
            print(f"{'='*60}")
            print(f"  Changed:   {report['changed_file']}")
            if report['changed_symbols']:
                print(f"  Symbols:   {', '.join(report['changed_symbols'])}")
            print(f"  Operation: {report['op_type']}")
            print(f"\n[DIRECT]  {report['direct_count']} file(s) directly affected:")
            for dep in report["direct_dependents"][:10]:
                print(f"  → {dep}")
            if report["indirect_count"] > 0:
                print(f"[INDIRECT] {report['indirect_count']} file(s) indirectly affected:")
                for dep in report["indirect_dependents"][:10]:
                    print(f"  ⤳ {dep}")
            if report["symbol_impacts"]:
                print(f"\n[SYMBOLS] Symbol-level impacts:")
                for si in report["symbol_impacts"][:5]:
                    print(f"  - {si['symbol']}: {si['affected_count']} file(s)")
            if report["semantic_similar"]:
                print(f"\n[FOCUS]   Semantically similar files (cos θ):")
                for ss in report["semantic_similar"][:5]:
                    sim = ss["similarity"]
                    print(f"  - {ss['file']}  sim={sim['value']} [{sim['state']}]  risk={ss['risk']}")
            print(f"\n{'─'*60}")
            print(f" AURA IMPACT (BBC Mathematics — State-Aware)")
            print(f"{'─'*60}")
            ir = aura['impact_ratio']
            cd = aura['chaos_density']
            pr = aura['pulse_risk']
            cr = aura['composite_risk']
            print(f"  Impact Ratio:    {ir['value']}  [{ir['state']}]")
            print(f"  Chaos Density:   {cd['value']}  [{cd['state']}]")
            print(f"  Pulse Risk:      {pr['value']}  [{pr['state']}]")
            print(f"  Composite Risk:  {cr['value']}  [{cr['state']}]")
            print(f"\n  VERDICT: {report['verdict_icon']} {report['verdict']}")
            print(f"{'='*60}")
            _print_transaction_report(project_resolved, "impact")
    elif args.command == "patch":
        project_resolved = str(Path(args.path).resolve())
        ctx_file = str(Path(project_resolved) / ".bbc" / "bbc_context.json")
        if not Path(ctx_file).exists():
            print(f"[BBC] Context not found: {ctx_file}")
            print(f"[BBC] Run 'bbc analyze' first.")
        else:
            from bbc_core.auto_patcher import AutoPatcher
            patcher = AutoPatcher(ctx_file, project_resolved)
            dry_run = not getattr(args, "apply", False)
            report = patcher.analyze_and_patch(dry_run=dry_run)
            mode_str = "DRY-RUN (preview)" if dry_run else "APPLY"
            oq = report["overall_quality"]
            print(f"\n{'='*60}")
            print(f" 🔧 BBC AUTO PATCHER [{mode_str}]")
            print(f"{'='*60}")
            print(f"  Total issues found: {report['total_patches']}")
            print(f"  Applied:            {report['applied']}")
            print(f"  Skipped (unsafe):   {report['skipped_unsafe']}")
            print(f"  Overall Quality:    {oq['value']}  [{oq['state']}]")
            if report["patch_results"]:
                print(f"\n{'─'*60}")
                print(f" PATCHES")
                print(f"{'─'*60}")
                for i, pr_item in enumerate(report["patch_results"], 1):
                    p = pr_item["patch"]
                    safe = "✅" if pr_item.get("safe_to_apply") else "🔴"
                    applied = " [APPLIED]" if pr_item.get("applied") else ""
                    print(f"  {i}. {safe} [{p['action']}] {p['file']}")
                    print(f"     {p['description']}{applied}")
                    if "patch_quality" in pr_item:
                        pq = pr_item["patch_quality"]
                        print(f"     Quality: {pq['value']} [{pq['state']}]")
            if report["reseal_needed"]:
                print(f"\n{'─'*60}")
                print(f" RESEAL NEEDED")
                print(f"{'─'*60}")
                for r in report["reseal_needed"]:
                    print(f"  ⚠️  {r['file']}: {r['description']}")
                print(f"\n  Run 'bbc analyze' to reseal context.")
            print(f"{'='*60}")
            if dry_run and report["total_patches"] > 0:
                print(f"\n  💡 To apply safe patches: bbc patch {args.path} --apply")
            _print_transaction_report(project_resolved, "patch")
    elif args.command == "hooks":
        from bbc_core.git_hooks import install_hooks, remove_hooks
        project_resolved = str(Path(args.path).resolve())
        if args.remove:
            result = remove_hooks(project_resolved)
            if result["removed"]:
                for r in result["removed"]:
                    print(f"[BBC] Removed: {r}")
            else:
                print("[BBC] No BBC hooks found to remove.")
        else:
            result = install_hooks(project_resolved)
            if result["success"]:
                for h in result["installed"]:
                    print(f"[BBC] Hook: {h}")
                print(f"[BBC] Hooks installed in {result['hooks_dir']}")
                _print_transaction_report(project_resolved, "hooks")
            else:
                for e in result.get("errors", []):
                    print(f"[BBC] Error: {e}")
    else:
        parser.print_help()

    # --- Telemetry: record command execution ---
    if _tele_command and _tele_command not in (
        "help", "telemetry", "doctor", "publish-check", "clean", "self-test",
        "integrations", "preview", "readiness", "security-check", "rule-health", None
    ):
        try:
            import json as _tele_json
            from bbc_core.telemetry import get_telemetry
            _tele_duration = time.time() - _tele_start
            _p = str(Path(getattr(args, 'path', '.')).resolve())
            _tele_log_path = str(Path(_p) / ".bbc" / "logs" / "telemetry.jsonl")
            _tele = get_telemetry(log_path=_tele_log_path)
            _tele_tokens = 0
            _tele_files = 0
            _tele_pct = 0.0
            try:
                _candidates = [
                    str(Path(_p) / ".bbc" / "bbc_context.json"),
                    str(Path(".").resolve() / ".bbc" / "bbc_context.json"),
                ]
                for _cf in _candidates:
                    if os.path.exists(_cf):
                        with open(_cf, "r", encoding="utf-8") as _f:
                            _cm = _tele_json.load(_f).get("metrics", {})
                        _tele_tokens = int(_cm.get("unified_tokens_saved", 0) or 0)
                        _tele_files = int(_cm.get("files_scanned", 0) or 0)
                        _tele_pct = float(_cm.get("unified_savings_pct", 0.0) or 0)
                        break
            except Exception:
                pass
            _tele.log_command(
                command=_tele_command,
                duration_sec=_tele_duration,
                files=_tele_files,
                tokens_saved=_tele_tokens,
                savings_pct=_tele_pct,
            )
        except Exception:
            pass

if __name__ == "__main__":
    main()
