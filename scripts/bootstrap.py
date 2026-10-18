"""Cross-platform, opt-in-safe project bootstrapper.

Installs Python dependencies declared in requirements*.txt (or the project extra),
checks required tools, and installs browser binaries only when requested.
It never uses sudo, never runs arbitrary shell installers, and does not install
unneeded language runtimes.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, text=True, check=check)


def requirements_files() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("requirements*.txt")
        if not any(part in {".venv", "venv", "node_modules", ".git"} for part in p.parts)
    )


def install_python_dependencies(dev: bool) -> None:
    files = requirements_files()
    if files:
        # Install all discovered requirement manifests; pip handles shared pins
        # and nested -r includes. This prevents a subproject manifest being missed.
        for path in files:
            if path.name == "requirements-dev.txt" and not dev:
                continue
            run([sys.executable, "-m", "pip", "install", "-r", str(path.relative_to(ROOT))])
    else:
        extra = '.[dev]' if dev else '.'
        run([sys.executable, "-m", "pip", "install", "-e", extra])


def check_runtime() -> None:
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12+ is required. Install it, then rerun this script.")
    if not shutil.which("git"):
        print("WARNING: git was not found. Git features will be unavailable.")
    if not shutil.which("litert-lm") and not shutil.which("litert_lm"):
        print("NOTICE: LiteRT-LM CLI was not found on PATH. Install it separately to run inference.")
        print("The bootstrapper intentionally does not guess an OS/CPU-specific model runtime installer.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install LiteRT Agent dependencies safely.")
    parser.add_argument("--dev", action="store_true", help="also install development/test tools")
    parser.add_argument("--browser", action="store_true", help="install Playwright Chromium browser")
    parser.add_argument("--check-only", action="store_true", help="check tools without installing packages")
    args = parser.parse_args()

    check_runtime()
    if args.check_only:
        return 0

    # Prefer the active interpreter; callers should activate a virtual environment first.
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    install_python_dependencies(args.dev)
    if args.browser:
        run([sys.executable, "-m", "playwright", "install", "chromium"])
    print("\\nBootstrap complete. Start the CLI with: litert-agent --help")
    print("Web UI, TUI, browser support, and inference runtimes are started only when invoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
