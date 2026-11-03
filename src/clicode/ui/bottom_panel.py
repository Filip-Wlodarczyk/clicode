from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass
from typing import Callable

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widgets import TabbedContent, TabPane, RichLog, Input, DataTable, Label, Static

from clicode.core.diagnostics import Diagnostic


class BottomPanel(Vertical):
    """Dolny panel z zakładkami: Terminal, Output, Debug Console, Błędy."""

    class ErrorSelected(Message):
        """Wiadomość wysyłana po kliknięciu błędu na liście."""
        def __init__(self, file_path: str, line: int, column: int):
            super().__init__()
            self.file_path = file_path
            self.line = line
            self.column = column

    class RunCommandRequested(Message):
        """Wiadomość z prośbą o wykonanie polecenia w terminalu."""
        def __init__(self, command: str):
            super().__init__()
            self.command = command

    DEFAULT_CSS = """
    BottomPanel {
        height: 14;
        dock: bottom;
        background: #11111b;
        border-top: solid #313244;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 0;
        height: 1fr;
    }
    #terminal-input-bar {
        height: 1;
        dock: bottom;
        background: #181825;
        border-top: solid #313244;
    }
    #term-prompt {
        width: 3;
        color: #a6e3a1;
        text-style: bold;
        padding-left: 1;
    }
    #term-input {
        width: 1fr;
        height: 1;
        border: none;
        background: transparent;
        color: #cdd6f4;
        padding: 0;
    }
    RichLog {
        background: #11111b;
        color: #cdd6f4;
        scrollbar-size: 1 1;
    }
    DataTable {
        background: #11111b;
        color: #cdd6f4;
        height: 1fr;
    }
    """

    def __init__(self, cwd: str, **kwargs):
        super().__init__(**kwargs)
        self.cwd = cwd
        self.diagnostics_list: list[Diagnostic] = []

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tab-problems", id="bottom-tabs"):
            with TabPane("Terminal (1)", id="tab-terminal"):
                yield RichLog(id="term-log", highlight=True, markup=True)
                with Horizontal(id="terminal-input-bar"):
                    yield Static("$ ", id="term-prompt")
                    yield Input(placeholder="Wpisz komendę shell i naciśnij Enter...", id="term-input")

            with TabPane("Output (2)", id="tab-output"):
                yield RichLog(id="output-log", highlight=True, markup=True)

            with TabPane("Debug Console (3)", id="tab-debug"):
                yield RichLog(id="debug-log", highlight=True, markup=True)

            with TabPane("Błędy / Problems (4)", id="tab-problems"):
                yield DataTable(id="problems-table")

    def on_mount(self) -> None:
        table = self.query_one("#problems-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Poziom", "Linia", "Kol", "Wiadomość", "Plik / Źródło")
        
        # Wiadomość powitalna w terminalu i debug
        term_log = self.query_one("#term-log", RichLog)
        term_log.write(f"[bold cyan]Wbudowany terminal clicode[/bold cyan] (katalog: {self.cwd})")
        term_log.write("[dim]Wpisz polecenie w dolnym pasku terminala i zatwierdź Enterem.[/dim]\n")

        debug_log = self.query_one("#debug-log", RichLog)
        debug_log.write("[green]✓ System diagnostyki i uruchamiania zainicjalizowany pomyślnie.[/green]")

    def switch_tab(self, tab_id: str) -> None:
        """Przełącza aktywną zakładkę w panelu dolnym."""
        tabs = self.query_one("#bottom-tabs", TabbedContent)
        mapping = {
            "terminal": "tab-terminal",
            "output": "tab-output",
            "debug": "tab-debug",
            "problems": "tab-problems",
            "1": "tab-terminal",
            "2": "tab-output",
            "3": "tab-debug",
            "4": "tab-problems",
        }
        target = mapping.get(tab_id.lower(), tab_id)
        try:
            tabs.active = target
            if target == "tab-terminal":
                self.query_one("#term-input", Input).focus()
        except Exception:
            pass

    def log_output(self, text: str, is_error: bool = False) -> None:
        """Wypisuje tekst do panelu Output."""
        output = self.query_one("#output-log", RichLog)
        if is_error:
            output.write(f"[red]{text}[/red]")
        else:
            output.write(text)

    def log_debug(self, text: str) -> None:
        """Wypisuje informację debugowania."""
        try:
            debug = self.query_one("#debug-log", RichLog)
            debug.write(f"[dim]{text}[/dim]")
        except Exception:
            pass

    def update_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        """Aktualizuje tabelę błędów / ostrzeżeń."""
        self.diagnostics_list = diagnostics
        table = self.query_one("#problems-table", DataTable)
        table.clear()

        # Zaktualizuj etykietę zakładki
        tabs = self.query_one("#bottom-tabs", TabbedContent)
        err_count = sum(1 for d in diagnostics if d.severity == "error")
        warn_count = sum(1 for d in diagnostics if d.severity == "warning")

        if not diagnostics:
            table.add_row("[green]✓ Brak[/green]", "-", "-", "Brak wykrytych błędów składniowych i lintera.", "")
            return

        for idx, d in enumerate(diagnostics):
            sev_badge = (
                "[bold red]❌ BŁĄD[/bold red]" if d.severity == "error"
                else "[yellow]⚠️ OSTRZ[/yellow]" if d.severity == "warning"
                else "[blue]ℹ️ INFO[/blue]"
            )
            file_disp = os.path.basename(d.file_path) if d.file_path else d.source
            table.add_row(
                sev_badge,
                str(d.line),
                str(d.column),
                d.message,
                f"{file_disp} ({d.source})",
                key=str(idx),
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Obsługa kliknięcia wiersza z błędem w tabeli."""
        key = event.row_key.value
        try:
            idx = int(key)
            if 0 <= idx < len(self.diagnostics_list):
                d = self.diagnostics_list[idx]
                self.post_message(self.ErrorSelected(d.file_path, d.line, d.column))
        except (ValueError, IndexError):
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Wykonanie polecenia w terminalu po naciśnięciu Enter."""
        cmd = event.value.strip()
        if not cmd:
            return
        event.input.value = ""
        term_log = self.query_one("#term-log", RichLog)
        term_log.write(f"[bold green]$ {cmd}[/bold green]")
        self.post_message(self.RunCommandRequested(cmd))
