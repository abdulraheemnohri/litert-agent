# Installation

Requires Python 3.12+. The bootstrapper creates/uses an isolated `.venv`, installs project Python dependencies from the repository's `requirements*.txt` manifests, and checks required tools. It does not run privileged commands or execute third-party shell installers.

## Windows (PowerShell)

```powershell
git clone https://github.com/abdulraheemnohri/litert-agent.git
cd litert-agent
.\scripts\install.ps1
# Include tests, lint and build tools:
.\scripts\install.ps1 --dev
# Install Playwright Chromium only if you need browser automation:
.\scripts\install.ps1 --browser
```

## Linux, macOS, WSL and Termux

```sh
git clone https://github.com/abdulraheemnohri/litert-agent.git
cd litert-agent
sh scripts/install.sh
# Include development tools:
sh scripts/install.sh --dev
# Install Playwright Chromium only when browser automation is needed:
sh scripts/install.sh --browser
```

The launcher uses the current `python3` and creates a project-local virtual environment. If Python 3.12+ is missing, install it with your operating system's trusted package manager, then rerun the launcher. On Windows, install Python from python.org or the Microsoft Store and enable PATH.

## Runtime policy

- **Python** is required. Dependencies are isolated in `.venv`.
- **LiteRT-LM CLI** is the only model backend and must be installed separately for inference. Its installation differs by operating system, CPU architecture, and supported release; the bootstrapper will not guess or run an unverified installer.
- **Playwright browser binaries** are installed only with `--browser`; browser automation is not launched during setup.
- **Node.js and other language runtimes are not installed by default.** Enable/install a runtime only when a specific feature requires it.
- The CLI, TUI, web server, browser and worker loops are launched only when requested/configured. Do not start every service at boot. Where multiple independent workers/services are explicitly enabled, they may run concurrently under the application's configured limits.

Check the environment without installing anything:

```sh
python scripts/bootstrap.py --check-only
```

Verify LiteRT-LM availability and the app setup:

```sh
litert-agent doctor
```

## Running

```sh
litert-agent run "your goal"
litert-agent web     # http://127.0.0.1:8765
litert-agent tui
```

## Development and tests

```sh
python scripts/bootstrap.py --dev
pytest -q
ruff check src tests
```
