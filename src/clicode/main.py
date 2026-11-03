from __future__ import annotations

import argparse
import sys
from pathlib import Path

from clicode import __version__
from clicode.app import CliCodeApp


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clicode",
        description="CLI Code - nowoczesny edytor kodu w terminalu (Linux TUI Code Editor)",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Ścieżka do folderu projektu lub pliku do otwarcia (domyślnie bieżący folder)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    initial_file: Path | None = None
    target_dir: Path

    if target_path.is_file():
        initial_file = target_path
        target_dir = target_path.parent
    elif target_path.is_dir():
        target_dir = target_path
    else:
        # Może nowy plik do utworzenia
        initial_file = target_path
        target_dir = target_path.parent

    app = CliCodeApp(target_dir=target_dir, initial_file=initial_file)
    app.run()


if __name__ == "__main__":
    main()
