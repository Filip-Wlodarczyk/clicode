from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class TopBar(Horizontal):
    """Top status bar: Git Repo, Project Name, File, Language and Mode."""

    DEFAULT_CSS = """
    TopBar {
        height: 1;
        dock: top;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 1;
    }
    .top-section {
        width: auto;
        margin-right: 2;
    }
    .badge-git {
        color: #a6e3a1;
        text-style: bold;
    }
    .badge-project {
        color: #89b4fa;
        text-style: bold;
    }
    .badge-file {
        color: #f9e2af;
    }
    .badge-lang {
        color: #cba6f7;
        text-style: bold;
    }
    .badge-mode {
        color: #f38ba8;
        text-style: bold;
    }
    .spacer {
        width: 1fr;
    }
    .shortcut-hint {
        color: #6c7086;
    }
    """

    def __init__(
        self,
        project_name: str = "",
        git_info: dict | None = None,
        file_name: str = "No file open",
        language: str = "None",
        mode: str = "NORMAL",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.git_info = git_info or {}
        self.file_name = file_name
        self.language = language
        self.mode = mode
        self.is_dirty = False

    def compose(self) -> ComposeResult:
        yield Static(self._format_project(), id="top-project", classes="top-section badge-project")
        yield Static(self._format_git(), id="top-git", classes="top-section badge-git")
        yield Static(self._format_file(), id="top-file", classes="top-section badge-file")
        yield Static("", classes="spacer")
        yield Static(self._format_lang(), id="top-lang", classes="top-section badge-lang")
        yield Static(self._format_mode(), id="top-mode", classes="top-section badge-mode")
        yield Static("[Space: Menu]", classes="shortcut-hint")

    def _format_project(self) -> str:
        return f"📁 {self.project_name}"

    def _format_git(self) -> str:
        if not self.git_info.get("is_git"):
            return "🌿 (no repo)"
        repo = self.git_info.get("repo_name", "")
        branch = self.git_info.get("branch", "")
        dirty = "*" if self.git_info.get("dirty") else ""
        return f"🌿 {repo}:{branch}{dirty}"

    def _format_file(self) -> str:
        dirty_mark = " ●" if self.is_dirty else ""
        return f"📄 {self.file_name}{dirty_mark}"

    def _format_lang(self) -> str:
        return f"🔤 {self.language}"

    def _format_mode(self) -> str:
        return f"[{self.mode}]"

    def update_info(
        self,
        project_name: str | None = None,
        git_info: dict | None = None,
        file_name: str | None = None,
        language: str | None = None,
        mode: str | None = None,
        is_dirty: bool | None = None,
    ) -> None:
        if project_name is not None:
            self.project_name = project_name
            self.query_one("#top-project", Static).update(self._format_project())
        if git_info is not None:
            self.git_info = git_info
            self.query_one("#top-git", Static).update(self._format_git())
        if is_dirty is not None:
            self.is_dirty = is_dirty
        if file_name is not None:
            self.file_name = file_name
            self.query_one("#top-file", Static).update(self._format_file())
        elif is_dirty is not None:
            self.query_one("#top-file", Static).update(self._format_file())
        if language is not None:
            self.language = language
            self.query_one("#top-lang", Static).update(self._format_lang())
        if mode is not None:
            self.mode = mode
            self.query_one("#top-mode", Static).update(self._format_mode())
