from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunCommand:
    title: str
    command: str
    description: str
    category: str


def detect_run_commands(project_dir: Path | str, current_file: str | None = None) -> list[RunCommand]:
    """Detects and returns a list of suggested run commands for the given project."""
    p = Path(project_dir).resolve()
    commands: list[RunCommand] = []

    curr_path = Path(current_file) if current_file else None
    curr_rel = curr_path.relative_to(p) if curr_path and curr_path.is_relative_to(p) else curr_path

    # 1. FLUTTER / DART
    pubspec = p / "pubspec.yaml"
    if pubspec.exists():
        has_flutter = shutil.which("flutter") is not None
        if has_flutter:
            commands.extend([
                RunCommand("Flutter Run", "flutter run", "Run app on default device", "Flutter"),
                RunCommand("Flutter Run (Linux)", "flutter run -d linux", "Run native Linux app", "Flutter"),
                RunCommand("Flutter Run (Chrome)", "flutter run -d chrome", "Run web version in Chrome", "Flutter"),
                RunCommand("Flutter Run with Dart Define", "flutter run --dart-define=FLAG123=true", "Run with --dart-define environment flag", "Flutter"),
                RunCommand("Flutter Test", "flutter test", "Run unit and widget tests", "Flutter"),
                RunCommand("Flutter Pub Get", "flutter pub get", "Fetch project dependencies", "Flutter"),
                RunCommand("Flutter Build APK", "flutter build apk", "Build Android APK package", "Flutter"),
                RunCommand("Flutter Analyze", "flutter analyze", "Analyze project for errors and warnings", "Flutter"),
            ])
        else:
            commands.extend([
                RunCommand("Dart Run", "dart run", "Run main Dart program", "Dart"),
                RunCommand("Dart Test", "dart test", "Run Dart tests", "Dart"),
                RunCommand("Dart Analyze", "dart analyze", "Static analysis of Dart code", "Dart"),
            ])

    # 2. PYTHON
    is_python = (
        (p / "pyproject.toml").exists()
        or (p / "requirements.txt").exists()
        or (p / "setup.py").exists()
        or (p / "main.py").exists()
        or (curr_path and curr_path.suffix == ".py")
    )
    if is_python:
        if curr_rel and str(curr_rel).endswith(".py"):
            commands.append(
                RunCommand(f"Python: Run current file ({curr_rel})", f"python3 {curr_rel}", "Run currently open Python file", "Python")
            )
        if (p / "main.py").exists():
            commands.append(RunCommand("Python: main.py", "python3 main.py", "Run main project script", "Python"))
        if (p / "app.py").exists():
            commands.append(RunCommand("Python: app.py", "python3 app.py", "Run app.py application", "Python"))
        commands.append(RunCommand("Python: Pytest", "pytest", "Run pytest unit tests", "Python"))

    # 3. NODE.JS / TYPESCRIPT
    pkg_json = p / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                for script_name in scripts.keys():
                    commands.append(
                        RunCommand(f"npm run {script_name}", f"npm run {script_name}", f"Script from package.json ({script_name})", "Node.js")
                    )
        except Exception:
            commands.append(RunCommand("npm start", "npm start", "Run npm project", "Node.js"))
            commands.append(RunCommand("npm test", "npm test", "Run npm tests", "Node.js"))

    # 4. RUST
    cargo_toml = p / "Cargo.toml"
    if cargo_toml.exists():
        commands.extend([
            RunCommand("Cargo Run", "cargo run", "Compile and run Rust project", "Rust"),
            RunCommand("Cargo Test", "cargo test", "Run Cargo tests", "Rust"),
            RunCommand("Cargo Build", "cargo build", "Compile project", "Rust"),
            RunCommand("Cargo Check", "cargo check", "Fast code validity check", "Rust"),
        ])

    # 5. GO
    go_mod = p / "go.mod"
    if go_mod.exists():
        commands.extend([
            RunCommand("Go Run", "go run .", "Run Go project", "Go"),
            RunCommand("Go Test", "go test ./...", "Run project tests", "Go"),
            RunCommand("Go Build", "go build", "Compile Go binary", "Go"),
        ])

    # 6. MAKEFILE / C / C++
    makefile = p / "Makefile"
    if makefile.exists():
        commands.extend([
            RunCommand("Make", "make", "Default makefile target", "Make"),
            RunCommand("Make Test", "make test", "Run make tests", "Make"),
            RunCommand("Make Clean", "make clean", "Clean build artifacts", "Make"),
        ])

    # 7. BASH / SHELL
    if curr_rel and str(curr_rel).endswith((".sh", ".bash")):
        commands.append(
            RunCommand(f"Bash: Run {curr_rel}", f"bash {curr_rel}", "Run current shell script", "Shell")
        )

    # 8. General git / info commands
    commands.append(RunCommand("Git Status", "git status", "Show git changes status", "Git"))
    commands.append(RunCommand("Git Diff", "git diff", "Show changes", "Git"))

    return commands
