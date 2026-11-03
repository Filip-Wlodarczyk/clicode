from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widgets import TextArea, Static


class CodeEditor(Vertical):
    """Główny obszar edytora kodu z paskiem statusu kursora."""

    class ContentChanged(Message):
        """Wysyłane gdy treść uległa zmianie."""
        def __init__(self, is_dirty: bool):
            super().__init__()
            self.is_dirty = is_dirty

    class CursorMoved(Message):
        """Wysyłane po zmianie pozycji kursora."""
        def __init__(self, line: int, column: int):
            super().__init__()
            self.line = line
            self.column = column

    DEFAULT_CSS = """
    CodeEditor {
        height: 1fr;
        background: #1e1e2e;
    }
    TextArea {
        height: 1fr;
        border: none;
        background: #1e1e2e;
    }
    #editor-status-bar {
        height: 1;
        dock: bottom;
        background: #181825;
        color: #a6adc8;
        padding: 0 1;
        border-top: solid #313244;
    }
    .status-item {
        margin-right: 2;
    }
    .spacer {
        width: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_file: Path | None = None
        self.saved_content: str = ""
        self.current_language: str = "python"

    def compose(self) -> ComposeResult:
        yield TextArea(
            "",
            id="code-text-area",
            language="python",
            theme="vscode_dark",
            show_line_numbers=True,
            soft_wrap=False,
        )
        with Horizontal(id="editor-status-bar"):
            yield Static("Ln 1, Col 1", id="status-cursor", classes="status-item")
            yield Static("0 linii", id="status-lines", classes="status-item")
            yield Static("", classes="spacer")
            yield Static("UTF-8", classes="status-item")
            yield Static("Spacje: 4", classes="status-item")
            yield Static("Python", id="status-lang", classes="status-item")

    def load_file(self, file_path: Path | str) -> bool:
        """Ładuje plik do edytora."""
        p = Path(file_path).resolve()
        try:
            content = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = p.read_text(encoding="latin-1")
            except Exception:
                return False
        except Exception:
            return False

        self.current_file = p
        self.saved_content = content
        
        ta = self.query_one("#code-text-area", TextArea)
        ta.text = content

        # Wykrycie języka po rozszerzeniu
        detected_lang = self._detect_language(p.suffix)
        self.set_language(detected_lang)
        self._update_status()
        self.post_message(self.ContentChanged(is_dirty=False))
        return True

    def save_file(self, target_path: Path | str | None = None) -> bool:
        """Zapisuje treść edytora do pliku."""
        p = Path(target_path) if target_path else self.current_file
        if not p:
            return False

        ta = self.query_one("#code-text-area", TextArea)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(ta.text, encoding="utf-8")
            self.saved_content = ta.text
            self.current_file = p
            self.post_message(self.ContentChanged(is_dirty=False))
            return True
        except Exception:
            return False

    def get_text(self) -> str:
        return self.query_one("#code-text-area", TextArea).text

    def set_language(self, lang: str) -> None:
        """Zmienia język podświetlania składni."""
        self.current_language = lang
        ta = self.query_one("#code-text-area", TextArea)
        # Mapowanie na dostępne języki TextArea
        ta_lang_map = {
            "dart": "rust",  # zbliżona składnia c-like
            "flutter": "rust",
            "typescript": "javascript",
            "js": "javascript",
            "py": "python",
            "sh": "bash",
            "shell": "bash",
            "c": "rust",
            "cpp": "rust",
        }
        target_lang = ta_lang_map.get(lang.lower(), lang.lower())
        if target_lang in ta.available_languages:
            try:
                ta.language = target_lang
            except Exception:
                pass
        
        # Aktualizacja etykiety w pasku statusu
        try:
            self.query_one("#status-lang", Static).update(lang.capitalize())
        except Exception:
            pass

    def jump_to(self, line: int, column: int = 1) -> None:
        """Przeskakuje kursorem do podanej linii i kolumny."""
        ta = self.query_one("#code-text-area", TextArea)
        try:
            # line i column są 1-indexed, cursor_location to (row, column) 0-indexed
            row = max(0, line - 1)
            col = max(0, column - 1)
            ta.cursor_location = (row, col)
            ta.focus()
            self._update_status()
        except Exception:
            pass

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Obsługa zmiany tekstu."""
        ta = event.text_area
        is_dirty = (ta.text != self.saved_content)
        self.post_message(self.ContentChanged(is_dirty=is_dirty))
        self._update_status()

    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        """Obsługa zmiany pozycji kursora."""
        self._update_status()

    def _update_status(self) -> None:
        try:
            ta = self.query_one("#code-text-area", TextArea)
            row, col = ta.cursor_location
            total_lines = ta.document.line_count
            self.query_one("#status-cursor", Static).update(f"Ln {row + 1}, Col {col + 1}")
            self.query_one("#status-lines", Static).update(f"{total_lines} linii")
        except Exception:
            pass

    def _detect_language(self, suffix: str) -> str:
        mapping = {
            ".py": "python",
            ".dart": "dart",
            ".js": "javascript",
            ".mjs": "javascript",
            ".ts": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
        }
        return mapping.get(suffix.lower(), "python")
