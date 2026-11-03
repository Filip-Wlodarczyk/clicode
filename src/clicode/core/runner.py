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
    """Wykrywa i zwraca listę sugerowanych poleceń uruchomieniowych dla danego projektu."""
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
                RunCommand("Flutter Run", "flutter run", "Uruchom aplikację na domyślnym urządzeniu", "Flutter"),
                RunCommand("Flutter Run (Linux)", "flutter run -d linux", "Uruchom natywną aplikację Linux", "Flutter"),
                RunCommand("Flutter Run (Chrome)", "flutter run -d chrome", "Uruchom wersję webową w przeglądarce Chrome", "Flutter"),
                RunCommand("Flutter Run with Dart Define", "flutter run --dart-define=FLAGA123=true", "Uruchom z flagą środowiskową --dart-define", "Flutter"),
                RunCommand("Flutter Test", "flutter test", "Uruchom testy jednostkowe i widżetów", "Flutter"),
                RunCommand("Flutter Pub Get", "flutter pub get", "Pobierz zależności projektu", "Flutter"),
                RunCommand("Flutter Build APK", "flutter build apk", "Skompiluj pakiet APK na Androida", "Flutter"),
                RunCommand("Flutter Analyze", "flutter analyze", "Sprawdź projekt pod kątem błędów i ostrzeżeń", "Flutter"),
            ])
        else:
            commands.extend([
                RunCommand("Dart Run", "dart run", "Uruchom główny program Dart", "Dart"),
                RunCommand("Dart Test", "dart test", "Uruchom testy Dart", "Dart"),
                RunCommand("Dart Analyze", "dart analyze", "Statyczna analiza kodu Dart", "Dart"),
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
                RunCommand(f"Python: Uruchom bieżący plik ({curr_rel})", f"python3 {curr_rel}", "Uruchom aktualnie otwarty plik Python", "Python")
            )
        if (p / "main.py").exists():
            commands.append(RunCommand("Python: main.py", "python3 main.py", "Uruchom główny skrypt projektu", "Python"))
        if (p / "app.py").exists():
            commands.append(RunCommand("Python: app.py", "python3 app.py", "Uruchom aplikację app.py", "Python"))
        commands.append(RunCommand("Python: Pytest", "pytest", "Uruchom testy jednostkowe pytest", "Python"))

    # 3. NODE.JS / TYPESCRIPT
    pkg_json = p / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                for script_name in scripts.keys():
                    commands.append(
                        RunCommand(f"npm run {script_name}", f"npm run {script_name}", f"Skrypt z package.json ({script_name})", "Node.js")
                    )
        except Exception:
            commands.append(RunCommand("npm start", "npm start", "Uruchom projekt npm", "Node.js"))
            commands.append(RunCommand("npm test", "npm test", "Uruchom testy npm", "Node.js"))

    # 4. RUST
    cargo_toml = p / "Cargo.toml"
    if cargo_toml.exists():
        commands.extend([
            RunCommand("Cargo Run", "cargo run", "Skompiluj i uruchom projekt Rust", "Rust"),
            RunCommand("Cargo Test", "cargo test", "Uruchom testy Cargo", "Rust"),
            RunCommand("Cargo Build", "cargo build", "Skompiluj projekt", "Rust"),
            RunCommand("Cargo Check", "cargo check", "Szybka weryfikacja poprawności kodu", "Rust"),
        ])

    # 5. GO
    go_mod = p / "go.mod"
    if go_mod.exists():
        commands.extend([
            RunCommand("Go Run", "go run .", "Uruchom projekt Go", "Go"),
            RunCommand("Go Test", "go test ./...", "Uruchom testy projektu", "Go"),
            RunCommand("Go Build", "go build", "Skompiluj binarkę Go", "Go"),
        ])

    # 6. MAKEFILE / C / C++
    makefile = p / "Makefile"
    if makefile.exists():
        commands.extend([
            RunCommand("Make", "make", "Domyślny cel makefile", "Make"),
            RunCommand("Make Test", "make test", "Uruchom testy make", "Make"),
            RunCommand("Make Clean", "make clean", "Wyczyść pliki kompilacji", "Make"),
        ])

    # 7. BASH / SHELL
    if curr_rel and str(curr_rel).endswith((".sh", ".bash")):
        commands.append(
            RunCommand(f"Bash: Uruchom {curr_rel}", f"bash {curr_rel}", "Uruchom bieżący skrypt powłoki", "Shell")
        )

    # 8. Ogólne komendy git / info
    commands.append(RunCommand("Git Status", "git status", "Pokaż status zmian git", "Git"))
    commands.append(RunCommand("Git Diff", "git diff", "Pokaż wprowadzone zmiany", "Git"))

    return commands
