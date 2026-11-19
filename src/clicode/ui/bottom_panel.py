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
    """Bottom panel with tabs: Terminal, Output, Debug Console, Problems."""

    class ErrorSelected(Message):
        """Message emitted when an error row is clicked."""
        def __init__(self, file_path: str, line: int, column: int):
            super().__init__()
            self.file_path = file_path
            self.line = line
            self.column = column

    class RunCommandRequested(Message):
        """Message requesting command execution in terminal."""
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
                    yield Input(placeholder="Type shell command and press Enter...", id="term-input")

            with TabPane("Output (2)", id="tab-output"):
                yield RichLog(id="output-log", highlight=True, markup=True)

            with TabPane("Debug Console (3)", id="tab-debug"):
                yield RichLog(id="debug-log", highlight=True, markup=True)

            with TabPane("Problems (4)", id="tab-problems"):
                yield DataTable(id="problems-table")

    def on_mount(self) -> None:
        table = self.query_one("#problems-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Severity", "Line", "Col", "Message", "File / Source")
        
        # Welcome message in terminal and debug
        term_log = self.query_one("#term-log", RichLog)
        term_log.write(f"[bold cyan]CliCode Embedded Terminal[/bold cyan] (cwd: {self.cwd})")
        term_log.write("[dim]Type a command in the bottom input bar and press Enter.[/dim]\n")

        debug_log = self.query_one("#debug-log", RichLog)
        debug_log.write("[green]✓ Diagnostics and runner system initialized successfully.[/green]")

    def switch_tab(self, tab_id: str) -> None:
        """Switches active tab in bottom panel."""
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
        """Writes text to Output panel."""
        output = self.query_one("#output-log", RichLog)
        if is_error:
            output.write(f"[red]{text}[/red]")
        else:
            output.write(text)

    def log_debug(self, text: str) -> None:
        """Writes debug message."""
        try:
            debug = self.query_one("#debug-log", RichLog)
            debug.write(f"[dim]{text}[/dim]")
        except Exception:
            pass

    def update_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        """Updates problems/warnings table."""
        self.diagnostics_list = diagnostics
        table = self.query_one("#problems-table", DataTable)
        table.clear()

        # Update tab label
        tabs = self.query_one("#bottom-tabs", TabbedContent)
        err_count = sum(1 for d in diagnostics if d.severity == "error")
        warn_count = sum(1 for d in diagnostics if d.severity == "warning")

        if not diagnostics:
            table.add_row("[green]✓ None[/green]", "-", "-", "No syntax or linter errors detected.", "")
            return

        for idx, d in enumerate(diagnostics):
            sev_badge = (
                "[bold red]❌ ERROR[/bold red]" if d.severity == "error"
                else "[yellow]⚠️ WARN[/yellow]" if d.severity == "warning"
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
        """Handle clicking error row in table."""
        key = event.row_key.value
        try:
            idx = int(key)
            if 0 <= idx < len(self.diagnostics_list):
                d = self.diagnostics_list[idx]
                self.post_message(self.ErrorSelected(d.file_path, d.line, d.column))
        except (ValueError, IndexError):
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Execute command in terminal after pressing Enter."""
        cmd = event.value.strip()
        if not cmd:
            return
        event.input.value = ""
        term_log = self.query_one("#term-log", RichLog)
        term_log.write(f"[bold green]$ {cmd}[/bold green]")
        self.post_message(self.RunCommandRequested(cmd))
