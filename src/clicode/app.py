from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, TextArea, Input

from clicode.core.diagnostics import Diagnostic, run_diagnostics
from clicode.core.git import get_git_info
from clicode.core.runner import detect_run_commands
from clicode.ui.bottom_panel import BottomPanel
from clicode.ui.editor import CodeEditor
from clicode.ui.modals import (
    BottomPanelPickerModal,
    FileFinderModal,
    HelpModal,
    LanguagePickerModal,
    NewFileModal,
    RunPickerModal,
)
from clicode.ui.sidebar import FilteredDirectoryTree, Sidebar
from clicode.ui.top_bar import TopBar


class CliCodeApp(App):
    """Main application of the CLI Code editor."""

    TITLE = "CLI Code"
    CSS = """
    Screen {
        background: #1e1e2e;
        color: #cdd6f4;
    }
    #main-container {
        height: 1fr;
    }
    #editor-container {
        height: 1fr;
    }
    .leader-active {
        border: solid #f9e2af;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "save_file", "Save", show=True),
        Binding("ctrl+p", "open_file_finder", "Find file", show=True),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+t", "toggle_bottom_panel", "Bottom panel", show=True),
        Binding("ctrl+space", "activate_leader", "Leader Menu", show=True),
        Binding("f1", "show_help", "Help", show=True),
        Binding("f2", "select_language", "Language", show=False),
        Binding("f5", "run_project", "Run", show=False),
        Binding("escape", "escape_action", "Normal Mode / Close", show=True),
    ]

    def __init__(self, target_dir: str | Path | None = None, initial_file: str | Path | None = None):
        super().__init__()
        self.project_dir = Path(target_dir or os.getcwd()).resolve()
        self.initial_file = Path(initial_file).resolve() if initial_file else None
        self.current_file_path: Path | None = None
        self.current_language: str = "python"
        self.is_leader_active: bool = False
        self.mode: str = "NORMAL"
        self.show_sidebar: bool = True
        self.show_bottom: bool = True

    def compose(self) -> ComposeResult:
        git_info = get_git_info(self.project_dir)
        yield TopBar(
            project_name=self.project_dir.name,
            git_info=git_info,
            file_name="No file open",
            language=self.current_language.capitalize(),
            mode=self.mode,
            id="top-bar",
        )
        with Horizontal(id="main-container"):
            yield Sidebar(self.project_dir, id="sidebar")
            with Vertical(id="editor-container"):
                yield CodeEditor(id="editor")
                yield BottomPanel(str(self.project_dir), id="bottom-panel")

    def on_mount(self) -> None:
        # If initial file was provided, open it
        if self.initial_file and self.initial_file.is_file():
            self.open_file(self.initial_file)
        else:
            # Open first project file if it exists (e.g. main.py, lib/main.dart)
            candidates = [
                self.project_dir / "lib" / "main.dart",
                self.project_dir / "main.py",
                self.project_dir / "index.js",
                self.project_dir / "src" / "main.rs",
                self.project_dir / "README.md",
            ]
            for c in candidates:
                if c.exists() and c.is_file():
                    self.open_file(c)
                    break

        # Refresh diagnostics
        self.run_current_diagnostics()

    def open_file(self, file_path: Path | str) -> None:
        """Opens specified file in the editor."""
        p = Path(file_path).resolve()
        editor = self.query_one("#editor", CodeEditor)
        if editor.load_file(p):
            self.current_file_path = p
            self.current_language = editor.current_language
            
            # Update top bar
            top = self.query_one("#top-bar", TopBar)
            rel_name = p.name
            top.update_info(
                file_name=rel_name,
                language=self.current_language.capitalize(),
                is_dirty=False,
            )
            # Run diagnostics
            self.run_current_diagnostics()

    def action_save_file(self) -> None:
        """Saves current file."""
        editor = self.query_one("#editor", CodeEditor)
        if not self.current_file_path:
            # Ask for file name
            self.action_new_file()
            return
        if editor.save_file(self.current_file_path):
            top = self.query_one("#top-bar", TopBar)
            git_info = get_git_info(self.project_dir)
            top.update_info(is_dirty=False, git_info=git_info)
            bottom = self.query_one("#bottom-panel", BottomPanel)
            bottom.log_debug(f"File saved: {self.current_file_path.name}")
            self.run_current_diagnostics()

    def action_escape_action(self) -> None:
        """Return to NORMAL mode and reset leader state."""
        self.is_leader_active = False
        self.set_mode("NORMAL")
        # Remove focus from editor input
        try:
            self.query_one("#editor", CodeEditor).blur()
        except Exception:
            pass

    def action_activate_leader(self) -> None:
        """Activate leader menu (Space)."""
        self.is_leader_active = True
        top = self.query_one("#top-bar", TopBar)
        top.update_info(mode="SPACE: [l/r/t/p/w/n/b/h]")

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        top = self.query_one("#top-bar", TopBar)
        top.update_info(mode=mode)

    def on_key(self, event) -> None:
        """Handle Space + l / r / t / etc. key sequences."""
        focused = self.focused

        # If cursor is in TextArea in typing mode, space inserts a space,
        # UNLESS we are in NORMAL mode or leader is active.
        is_in_textarea = isinstance(focused, TextArea)
        is_in_input = isinstance(focused, Input)

        if self.is_leader_active:
            # Leader sequence after pressing Space
            self.is_leader_active = False
            top = self.query_one("#top-bar", TopBar)
            top.update_info(mode=self.mode)

            key = event.key.lower()
            if key == "l":
                self.action_select_language()
                event.prevent_default()
                event.stop()
            elif key == "r":
                self.action_run_project()
                event.prevent_default()
                event.stop()
            elif key == "t":
                self.action_select_bottom_panel()
                event.prevent_default()
                event.stop()
            elif key == "p":
                self.action_open_file_finder()
                event.prevent_default()
                event.stop()
            elif key == "w":
                self.action_save_file()
                event.prevent_default()
                event.stop()
            elif key == "n":
                self.action_new_file()
                event.prevent_default()
                event.stop()
            elif key == "b":
                self.action_toggle_sidebar()
                event.prevent_default()
                event.stop()
            elif key == "h":
                self.action_show_help()
                event.prevent_default()
                event.stop()
            return

        # If in NORMAL mode (and not in an Input) space was pressed:
        if event.key == "space" and not is_in_input and self.mode == "NORMAL":
            self.action_activate_leader()
            event.prevent_default()
            event.stop()
            return

        # If in NORMAL mode 'i' was pressed in editor -> switch to EDIT mode
        if self.mode == "NORMAL" and event.key == "i" and not is_in_input:
            self.set_mode("EDIT")
            self.query_one(TextArea).focus()
            event.prevent_default()
            event.stop()
            return

    def action_select_language(self) -> None:
        """Opens language selection modal (Space + l)."""
        def _on_lang_picked(lang: str | None) -> None:
            if not lang:
                return
            self.current_language = lang
            editor = self.query_one("#editor", CodeEditor)
            editor.set_language(lang)
            top = self.query_one("#top-bar", TopBar)
            top.update_info(language=lang.capitalize())
            bottom = self.query_one("#bottom-panel", BottomPanel)
            bottom.log_debug(f"Selected language: {lang.capitalize()}")
            # Refresh diagnostics with new language
            self.run_current_diagnostics()

        self.push_screen(LanguagePickerModal(), _on_lang_picked)

    def action_run_project(self) -> None:
        """Opens run project modal (Space + r)."""
        commands = detect_run_commands(self.project_dir, str(self.current_file_path) if self.current_file_path else None)

        def _on_command_picked(cmd: str | None) -> None:
            if not cmd:
                return
            self.execute_command(cmd)

        self.push_screen(RunPickerModal(commands), _on_command_picked)

    def action_select_bottom_panel(self) -> None:
        """Opens bottom panel selection modal (Space + t)."""
        def _on_panel_picked(panel: str | None) -> None:
            if not panel:
                return
            if panel == "toggle":
                self.action_toggle_bottom_panel()
                return
            bottom = self.query_one("#bottom-panel", BottomPanel)
            bottom.styles.display = "block"
            bottom.switch_tab(panel)

        self.push_screen(BottomPanelPickerModal(), _on_panel_picked)

    def action_open_file_finder(self) -> None:
        """Opens quick file finder (Space + p)."""
        def _on_file_selected(file_path: str | None) -> None:
            if file_path:
                self.open_file(Path(file_path))

        self.push_screen(FileFinderModal(self.project_dir), _on_file_selected)

    def action_new_file(self) -> None:
        """Create new file (Space + n)."""
        def _on_new_file_entered(filename: str | None) -> None:
            if not filename:
                return
            new_path = self.project_dir / filename
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.touch()
                sidebar = self.query_one("#sidebar", Sidebar)
                sidebar.reload()
                self.open_file(new_path)
            except Exception as e:
                bottom = self.query_one("#bottom-panel", BottomPanel)
                bottom.log_output(f"Error creating file: {e}", is_error=True)

        self.push_screen(NewFileModal(), _on_new_file_entered)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", Sidebar)
        self.show_sidebar = not self.show_sidebar
        sidebar.styles.display = "block" if self.show_sidebar else "none"

    def action_toggle_bottom_panel(self) -> None:
        bottom = self.query_one("#bottom-panel", BottomPanel)
        self.show_bottom = not self.show_bottom
        bottom.styles.display = "block" if self.show_bottom else "none"

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    # --- Widget event handlers ---

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Click on file in file tree on the left."""
        self.open_file(event.path)

    def on_code_editor_content_changed(self, event: CodeEditor.ContentChanged) -> None:
        """Editor content changed."""
        top = self.query_one("#top-bar", TopBar)
        top.update_info(is_dirty=event.is_dirty)

    def on_bottom_panel_error_selected(self, event: BottomPanel.ErrorSelected) -> None:
        """Click on problem row in table."""
        if event.file_path and os.path.exists(event.file_path):
            if not self.current_file_path or Path(event.file_path).resolve() != self.current_file_path.resolve():
                self.open_file(event.file_path)
        editor = self.query_one("#editor", CodeEditor)
        editor.jump_to(event.line, event.column)

    def on_bottom_panel_run_command_requested(self, event: BottomPanel.RunCommandRequested) -> None:
        """Execute command from terminal bar."""
        self.execute_command(event.command, target_tab="terminal")

    # --- Background tasks (Worker) ---

    @work(exclusive=True, group="diagnostics")
    async def run_current_diagnostics(self) -> None:
        """Runs linter/compiler analysis for the open file."""
        editor = self.query_one("#editor", CodeEditor)
        content = editor.get_text()
        file_path = self.current_file_path
        lang = self.current_language

        loop = asyncio.get_event_loop()
        diags = await loop.run_in_executor(None, run_diagnostics, file_path, content, lang)

        bottom = self.query_one("#bottom-panel", BottomPanel)
        bottom.update_diagnostics(diags)

    @work(exclusive=False)
    async def execute_command(self, cmd: str, target_tab: str = "output") -> None:
        """Asynchronously runs a system command and streams output to bottom panel."""
        bottom = self.query_one("#bottom-panel", BottomPanel)
        bottom.styles.display = "block"
        bottom.switch_tab(target_tab)

        if target_tab == "output":
            bottom.log_output(f"\n[bold green]▶ Running:[/] [cyan]{cmd}[/]\n")
        
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_dir),
            )

            async def _stream_pipe(pipe, is_err: bool):
                while True:
                    line = await pipe.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").rstrip()
                    if target_tab == "output":
                        bottom.log_output(text, is_error=is_err)
                    else:
                        term_log = bottom.query_one("#term-log")
                        term_log.write(f"[red]{text}[/red]" if is_err else text)

            await asyncio.gather(
                _stream_pipe(process.stdout, False),
                _stream_pipe(process.stderr, True),
            )
            ret = await process.wait()
            status_color = "green" if ret == 0 else "red"
            msg = f"\n[{status_color}]■ Finished with exit code {ret}[/{status_color}]\n"
            if target_tab == "output":
                bottom.log_output(msg)
            else:
                bottom.query_one("#term-log").write(msg)

            # Refresh git repo status and file tree
            top = self.query_one("#top-bar", TopBar)
            top.update_info(git_info=get_git_info(self.project_dir))
            sidebar = self.query_one("#sidebar", Sidebar)
            sidebar.reload()

        except Exception as e:
            bottom.log_output(f"[bold red]Command execution error:[/] {e}", is_error=True)
