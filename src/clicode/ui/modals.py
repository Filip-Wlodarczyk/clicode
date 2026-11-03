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
    """Modal wyboru języka programowania (Spacja + l)."""

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
            yield Label("🔤 Wybierz język projektu / pliku (Spacja + l):", id="lang-title")
            yield Input(placeholder="Filtruj języki (np. dart, python, rust)...", id="lang-filter")
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

            # Sprawdzenie dostępnych narzędzi w systemie
            installed = [t for t in item["tools"] if shutil.which(t)]
            if installed:
                status = f"[green]✓ {', '.join(installed)}[/green]"
            else:
                status = "[dim]wbudowany parser[/dim]"

            label = f"[bold]{name}[/bold]  [dim]({item['ext']})[/dim]  |  Narzędzia: {status}"
            option_list.add_option(Option(prompt=label, id=lid))

    def on_input_changed(self, event: Input.Changed) -> None:
        self._populate_list(event.value)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option_id))

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class RunPickerModal(ModalScreen[str | None]):
    """Modal wyboru komendy uruchomienia (Spacja + r)."""

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
            yield Label("🚀 Uruchom projekt / zadanie (Spacja + r):", id="run-title")
            yield Input(placeholder="Wpisz własną komendę lub flagi (np. flutter run --dart-define=FLAGA123=true)...", id="custom-cmd-input")
            yield OptionList(id="run-list")
            yield Label("[Enter] Wybierz / Uruchom  |  [Esc] Anuluj", id="run-hint")

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
    """Menu wyboru dolnego panelu (Spacja + t): Terminal, Output, Debug, Błędy."""

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
            yield Label("🖥️ Wybierz widok panelu dolnego (Spacja + t):", id="panel-title")
            yield OptionList(
                Option("[bold green]1. Terminal[/bold green]          - Interaktywna powłoka shell", id="terminal"),
                Option("[bold cyan]2. Output[/bold cyan]            - Wyjście uruchomień i zadań", id="output"),
                Option("[bold magenta]3. Debug Console[/bold magenta]     - Konsola debugowania i logów", id="debug"),
                Option("[bold red]4. Błędy / Problems[/bold red] - Lista błędów i ostrzeżeń lintera", id="problems"),
                Option("[bold yellow]5. Przełącz / Ukryj[/bold yellow]   - Schowaj lub pokaż panel dolny", id="toggle"),
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
    """Szybkie wyszukiwanie plików w projekcie (Spacja + p / Ctrl+p)."""

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
            yield Label("🔍 Szybkie otwarcie pliku (Spacja + p):", id="finder-title")
            yield Input(placeholder="Wpisz fragment nazwy pliku...", id="finder-input")
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
    """Tworzenie nowego pliku (Spacja + n)."""

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
            yield Label("📄 Utwórz nowy plik:", id="newfile-title")
            yield Input(placeholder="Wpisz nazwę (np. main.py, lib/app.dart)...", id="newfile-input")

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
    """Menu pomocy ze skrótami klawiszowymi (Spacja + h / F1)."""

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
[bold yellow]CLI CODE - Przewodnik po skrótach klawiszowych:[/bold yellow]

[bold cyan]Menu Lidera (naciśnij Spację w trybie NORMAL lub Ctrl+Space):[/bold cyan]
  [bold]Spacja + l[/bold] : Wybór języka (zmienia składnię i uruchamia diagnostykę)
  [bold]Spacja + r[/bold] : Uruchom projekt (komendy Flutter, Python, Node, Cargo itp.)
  [bold]Spacja + t[/bold] : Menu dolnych paneli (Terminal, Output, Debug, Błędy)
  [bold]Spacja + p[/bold] : Szybkie wyszukiwanie plików w projekcie
  [bold]Spacja + w[/bold] : Zapisz bieżący plik
  [bold]Spacja + n[/bold] : Utwórz nowy plik
  [bold]Spacja + b[/bold] : Pokaż / ukryj lewy pasek boczny z plikami
  [bold]Spacja + h[/bold] : To okno pomocy

[bold cyan]Skróty bezpośrednie:[/bold cyan]
  [bold]Ctrl + S[/bold]   : Zapisz plik
  [bold]Ctrl + P[/bold]   : Szukaj pliku
  [bold]Ctrl + B[/bold]   : Przełącz pasek boczny
  [bold]Ctrl + T[/bold]   : Przełącz panel dolny
  [bold]Ctrl + Q[/bold]   : Wyjdź z edytora
  [bold]Esc[/bold]        : Powrót do trybu NORMAL ze skrótami Spacji
  [bold]i / Enter[/bold]  : Przejście do edycji tekstu

Naciśnij [bold green]Esc[/bold green] lub [bold green]Enter[/bold green], aby zamknąć to okno.
"""

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Label("💡 Pomoc i skróty CLI Code", id="help-title")
            yield Static(self.HELP_TEXT, id="help-content")

    def on_key(self, event) -> None:
        if event.key in ("escape", "enter", "space"):
            self.dismiss(None)
