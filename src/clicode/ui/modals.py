from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Grid
from textual.screen import ModalScreen
from textual.widgets import Input, ListView, ListItem, Label, Button, Static, OptionList
from textual.widgets.option_list import Option

from clicode.core.runner import RunCommand


SUPPORTED_LANGUAGES = [
    {"name": "Python", "id": "python", "ext": ".py", "tools": ["python3", "ruff", "flake8", "mypy"]},
    {"name": "Dart / Flutter", "id": "dart", "ext": ".dart", "tools": ["dart", "flutter"]},
    {"name": "JavaScript", "id": "javascript", "ext": ".js", "tools": ["node", "npm", "eslint"]},
    {"name": "TypeScript", "id": "typescript", "ext": ".ts", "tools": ["tsc", "node"]},
    {"name": "Rust", "id": "rust", "ext": ".rs", "tools": ["cargo", "rustc"]},
    {"name": "Go", "id": "go", "ext": ".go", "tools": ["go", "gopls"]},
    {"name": "Bash / Shell", "id": "bash", "ext": ".sh", "tools": ["bash", "shellcheck"]},
    {"name": "C / C++", "id": "c", "ext": ".c", "tools": ["gcc", "clang", "g++"]},
    {"name": "JSON", "id": "json", "ext": ".json", "tools": ["python3"]},
    {"name": "YAML", "id": "yaml", "ext": ".yaml", "tools": ["python3"]},
    {"name": "TOML", "id": "toml", "ext": ".toml", "tools": ["python3"]},
    {"name": "Markdown", "id": "markdown", "ext": ".md", "tools": []},
    {"name": "HTML", "id": "html", "ext": ".html", "tools": []},
    {"name": "CSS", "id": "css", "ext": ".css", "tools": []},
    {"name": "SQL", "id": "sql", "ext": ".sql", "tools": []},
]


class LanguagePickerModal(ModalScreen[str | None]):
    """Modal for selecting programming language (Space + l)."""

    DEFAULT_CSS = """
    LanguagePickerModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #lang-dialog {
        width: 65;
        height: 24;
        background: #1e1e2e;
        border: thick #89b4fa;
        padding: 1 2;
    }
    #lang-title {
        text-style: bold;
        color: #89b4fa;
        margin-bottom: 1;
    }
    #lang-filter {
        margin-bottom: 1;
        background: #181825;
        border: solid #45475a;
        color: #cdd6f4;
    }
    #lang-list {
        height: 1fr;
        background: #11111b;
        border: solid #313244;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="lang-dialog"):
            yield Label("🔤 Select project / file language (Space + l):", id="lang-title")
            yield Input(placeholder="Filter languages (e.g. dart, python, rust)...", id="lang-filter")
            yield OptionList(id="lang-list")

    def on_mount(self) -> None:
        self._populate_list("")
        self.query_one("#lang-filter", Input).focus()

    def _populate_list(self, filter_text: str) -> None:
        option_list = self.query_one("#lang-list", OptionList)
        option_list.clear_options()
        f_lower = filter_text.lower().strip()

        for item in SUPPORTED_LANGUAGES:
            name = item["name"]
            lid = item["id"]
            if f_lower and f_lower not in name.lower() and f_lower not in lid:
                continue

            # Check available tools in system PATH
            installed = [t for t in item["tools"] if shutil.which(t)]
            if installed:
                status = f"[green]✓ {', '.join(installed)}[/green]"
            else:
                status = "[dim]built-in parser[/dim]"

            label = f"[bold]{name}[/bold]  [dim]({item['ext']})[/dim]  |  Tools: {status}"
            option_list.add_option(Option(prompt=label, id=lid))

    def on_input_changed(self, event: Input.Changed) -> None:
        self._populate_list(event.value)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option_id))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class RunPickerModal(ModalScreen[str | None]):
    """Modal for selecting run command (Space + r)."""

    DEFAULT_CSS = """
    RunPickerModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #run-dialog {
        width: 76;
        height: 26;
        background: #1e1e2e;
        border: thick #a6e3a1;
        padding: 1 2;
    }
    #run-title {
        text-style: bold;
        color: #a6e3a1;
        margin-bottom: 1;
    }
    #custom-cmd-input {
        margin-bottom: 1;
        background: #181825;
        border: solid #45475a;
        color: #cdd6f4;
    }
    #run-list {
        height: 1fr;
        background: #11111b;
        border: solid #313244;
    }
    #run-hint {
        color: #6c7086;
        margin-top: 1;
    }
    """

    def __init__(self, commands: list[RunCommand], **kwargs):
        super().__init__(**kwargs)
        self.commands = commands

    def compose(self) -> ComposeResult:
        with Vertical(id="run-dialog"):
            yield Label("🚀 Run project / task (Space + r):", id="run-title")
            yield Input(placeholder="Type custom command or flags (e.g. flutter run --dart-define=FLAG123=true)...", id="custom-cmd-input")
            yield OptionList(id="run-list")
            yield Label("[Enter] Select / Run  |  [Esc] Cancel", id="run-hint")

    def on_mount(self) -> None:
        option_list = self.query_one("#run-list", OptionList)
        for idx, cmd in enumerate(self.commands):
            cat_color = "#89b4fa" if cmd.category == "Flutter" else "#f9e2af" if cmd.category == "Python" else "#a6e3a1"
            prompt = f"[{cat_color}][{cmd.category}][/{cat_color}] [bold]{cmd.command}[/bold] - [dim]{cmd.description}[/dim]"
            option_list.add_option(Option(prompt=prompt, id=str(idx)))
        self.query_one("#custom-cmd-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if cmd:
            self.dismiss(cmd)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        idx = int(str(event.option_id))
        self.dismiss(self.commands[idx].command)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class BottomPanelPickerModal(ModalScreen[str | None]):
    """Menu for selecting bottom panel (Space + t): Terminal, Output, Debug, Problems."""

    DEFAULT_CSS = """
    BottomPanelPickerModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #panel-dialog {
        width: 55;
        height: 18;
        background: #1e1e2e;
        border: thick #f9e2af;
        padding: 1 2;
    }
    #panel-title {
        text-style: bold;
        color: #f9e2af;
        margin-bottom: 1;
    }
    #panel-list {
        height: 1fr;
        background: #11111b;
        border: solid #313244;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="panel-dialog"):
            yield Label("🖥️ Select bottom panel view (Space + t):", id="panel-title")
            yield OptionList(
                Option("[bold green]1. Terminal[/bold green]          - Interactive shell console", id="terminal"),
                Option("[bold cyan]2. Output[/bold cyan]            - Run and task output", id="output"),
                Option("[bold magenta]3. Debug Console[/bold magenta]     - Debug console and logs", id="debug"),
                Option("[bold red]4. Problems[/bold red]          - Linter errors and warnings list", id="problems"),
                Option("[bold yellow]5. Toggle / Hide[/bold yellow]     - Show or hide bottom panel", id="toggle"),
                id="panel-list",
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option_id))

    def on_key(self, event) -> None:
        if event.key in ("1", "t"):
            self.dismiss("terminal")
        elif event.key in ("2", "o"):
            self.dismiss("output")
        elif event.key in ("3", "d"):
            self.dismiss("debug")
        elif event.key in ("4", "b", "p"):
            self.dismiss("problems")
        elif event.key == "escape":
            self.dismiss(None)


class FileFinderModal(ModalScreen[str | None]):
    """Quick file finder in project (Space + p / Ctrl+p)."""

    DEFAULT_CSS = """
    FileFinderModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #finder-dialog {
        width: 70;
        height: 22;
        background: #1e1e2e;
        border: thick #cba6f7;
        padding: 1 2;
    }
    #finder-title {
        text-style: bold;
        color: #cba6f7;
        margin-bottom: 1;
    }
    #finder-input {
        margin-bottom: 1;
        background: #181825;
        border: solid #45475a;
        color: #cdd6f4;
    }
    #finder-list {
        height: 1fr;
        background: #11111b;
        border: solid #313244;
    }
    """

    def __init__(self, root_dir: Path | str, **kwargs):
        super().__init__(**kwargs)
        self.root_dir = Path(root_dir).resolve()
        self.all_files: list[Path] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="finder-dialog"):
            yield Label("🔍 Quick open file (Space + p):", id="finder-title")
            yield Input(placeholder="Type file name fragment...", id="finder-input")
            yield OptionList(id="finder-list")

    def on_mount(self) -> None:
        ignored = {".git", ".venv", "node_modules", "__pycache__", ".dart_tool", "build"}
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignored and not d.startswith(".git")]
            for f in files:
                full = Path(root) / f
                self.all_files.append(full)
        self._filter("")
        self.query_one("#finder-input", Input).focus()

    def _filter(self, query: str) -> None:
        option_list = self.query_one("#finder-list", OptionList)
        option_list.clear_options()
        q = query.lower().strip()
        count = 0
        for p in self.all_files:
            rel = p.relative_to(self.root_dir)
            rel_str = str(rel)
            if not q or q in rel_str.lower():
                option_list.add_option(Option(prompt=f"📄 {rel_str}", id=str(p)))
                count += 1
                if count >= 40:
                    break

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter(event.value)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option_id))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class NewFileModal(ModalScreen[str | None]):
    """Create a new file (Space + n)."""

    DEFAULT_CSS = """
    NewFileModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #newfile-dialog {
        width: 50;
        height: 12;
        background: #1e1e2e;
        border: thick #89b4fa;
        padding: 1 2;
    }
    #newfile-title {
        text-style: bold;
        color: #89b4fa;
        margin-bottom: 1;
    }
    #newfile-input {
        background: #181825;
        border: solid #45475a;
        color: #cdd6f4;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="newfile-dialog"):
            yield Label("📄 Create new file:", id="newfile-title")
            yield Input(placeholder="Enter name (e.g. main.py, lib/app.dart)...", id="newfile-input")

    def on_mount(self) -> None:
        self.query_one("#newfile-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if name:
            self.dismiss(name)
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class HelpModal(ModalScreen[None]):
    """Help menu with keyboard shortcuts (Space + h / F1)."""

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #help-dialog {
        width: 72;
        height: 25;
        background: #1e1e2e;
        border: thick #f38ba8;
        padding: 1 2;
    }
    #help-title {
        text-style: bold;
        color: #f38ba8;
        margin-bottom: 1;
    }
    #help-content {
        height: 1fr;
        color: #cdd6f4;
        background: #11111b;
        padding: 1;
        border: solid #313244;
    }
    """

    HELP_TEXT = """
[bold yellow]CLI CODE - Keyboard Shortcuts Guide:[/bold yellow]

[bold cyan]Leader Menu (press Space in NORMAL mode or Ctrl+Space):[/bold cyan]
  [bold]Space + l[/bold] : Select language (changes syntax and runs diagnostics)
  [bold]Space + r[/bold] : Run project (Flutter, Python, Node, Cargo commands etc.)
  [bold]Space + t[/bold] : Bottom panels menu (Terminal, Output, Debug, Problems)
  [bold]Space + p[/bold] : Quick search and open files in project
  [bold]Space + w[/bold] : Save current file
  [bold]Space + n[/bold] : Create new file
  [bold]Space + b[/bold] : Show / hide left sidebar with files
  [bold]Space + h[/bold] : This help window

[bold cyan]Direct Shortcuts:[/bold cyan]
  [bold]Ctrl + S[/bold]   : Save file
  [bold]Ctrl + P[/bold]   : Find file
  [bold]Ctrl + B[/bold]   : Toggle sidebar
  [bold]Ctrl + T[/bold]   : Toggle bottom panel
  [bold]Ctrl + Q[/bold]   : Quit editor
  [bold]Esc[/bold]        : Return to NORMAL mode (Space shortcuts active)
  [bold]i / Enter[/bold]  : Enter text edit mode (EDIT)

Press [bold green]Esc[/bold green] or [bold green]Enter[/bold green] to close this window.
"""

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("💡 CLI Code Help and Shortcuts", id="help-title")
            yield Static(self.HELP_TEXT, id="help-content")

    def on_key(self, event) -> None:
        if event.key in ("escape", "enter", "space"):
            self.dismiss(None)
