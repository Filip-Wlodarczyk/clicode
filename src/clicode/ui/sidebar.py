from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DirectoryTree, Label, Static


IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".dart_tool", "build", ".idea", ".vscode"}


class FilteredDirectoryTree(DirectoryTree):
    """Drzewo katalogów filtrujące niepotrzebne foldery (np. .git, node_modules)."""

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        return [
            p for p in paths
            if p.name not in IGNORED_DIRS and not p.name.startswith(".git")
        ]


class Sidebar(Vertical):
    """Lewy panel boczny z drzewem plików projektu."""

    DEFAULT_CSS = """
    Sidebar {
        width: 32;
        dock: left;
        background: #181825;
        border-right: solid #313244;
    }
    #sidebar-header {
        height: 2;
        padding: 0 1;
        background: #11111b;
        color: #89b4fa;
        text-style: bold;
        content-align: left middle;
        border-bottom: solid #313244;
    }
    FilteredDirectoryTree {
        background: transparent;
        color: #cdd6f4;
        scrollbar-size: 1 1;
    }
    FilteredDirectoryTree > .tree--cursor {
        background: #313244;
        color: #f5e0dc;
        text-style: bold;
    }
    """

    def __init__(self, root_path: Path | str, **kwargs):
        super().__init__(**kwargs)
        self.root_path = Path(root_path).resolve()

    def compose(self) -> ComposeResult:
        yield Label(f"📁 {self.root_path.name}", id="sidebar-header")
        yield FilteredDirectoryTree(str(self.root_path), id="file-tree")

    def reload(self) -> None:
        """Odświeża drzewo plików."""
        tree = self.query_one("#file-tree", FilteredDirectoryTree)
        tree.reload()
