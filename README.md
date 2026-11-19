# CLI Code 💻🚀

Modern, fast, and feature-rich terminal code editor (Linux TUI Code Editor).

## 🌟 Features

- **Project file tree** on the left with filtering and instant file opening.
- **Top status bar**:
  - Project and directory name
  - Git repository and active branch (with dirty/clean status `*`)
  - Active file and unsaved changes indicator `●`
  - Current programming language
  - Editor mode (`NORMAL` / `EDIT`)
- **Bottom panel bar (`Space + t`)**:
  - `Terminal`: built-in interactive shell console to run commands
  - `Output`: stdout/stderr stream of executed tasks and projects
  - `Debug Console`: logs and event history
  - `Problems`: table with linter/compiler errors and warnings; clicking navigates directly to the error line!
- **Language selection (`Space + l`)**:
  - Support for Python, Dart / Flutter, JavaScript, TypeScript, Rust, Go, C/C++, Bash, JSON, YAML, TOML, and more.
  - Automatic code analysis via installed system tools (`dart analyze`, `python3`, `ruff`, `gcc`, etc.).
- **Project runner (`Space + r`)**:
  - Smart project detection:
    - **Flutter**: `flutter run`, `flutter run -d linux`, `flutter run -d chrome`, `flutter run --dart-define=FLAG123=true`, `flutter test`, `flutter pub get`
    - **Python**: `python3 <file>`, `pytest`, `python3 main.py`
    - **Node.js**: scripts from `package.json` (`npm start`, `npm run dev`, `npm test`)
    - **Rust**: `cargo run`, `cargo test`
    - **Go**: `go run .`, `go test`
    - Any custom command and flags.
- **Quick file finder (`Space + p` / `Ctrl + p`)**:
  - Fast file search across the project.
- **Create new files (`Space + n`)**.
- **Saving (`Space + w` / `Ctrl + s`)**.
- **Help and shortcuts (`Space + h` / `F1`)**.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Space + l` | Select language menu |
| `Space + r` | Run project menu |
| `Space + t` | Switch bottom panels (Terminal, Output, Debug, Problems) |
| `Space + p` | Quick search and open file |
| `Space + w` | Save file |
| `Space + n` | New file |
| `Space + b` | Show / hide file sidebar |
| `Space + h` / `F1` | Help and shortcuts window |
| `Ctrl + S` | Save file |
| `Ctrl + P` | Find file |
| `Ctrl + B` | Toggle sidebar |
| `Ctrl + T` | Toggle bottom panel |
| `Ctrl + Q` | Quit editor |
| `Esc` | Return to NORMAL mode |
| `i` / `Enter` | Enter edit mode (EDIT) |

---

## 📦 Installation

To install CLI Code locally:

```bash
git clone <repository-url>
cd clicode
pip install -e .
```

### Requirements
- Python 3.10+
- Terminal with truecolor support (e.g. Kitty, Alacritty, GNOME Terminal, WezTerm)

---

## 🚀 Usage

You can launch the editor from any directory:
```bash
clicode
```

You can also specify a target folder or file:
```bash
clicode /path/to/project
# or
clicode main.py
```
