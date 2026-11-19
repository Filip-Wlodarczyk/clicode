from __future__ import annotations

import os
import subprocess
from pathlib import Path


def get_git_info(path: Path | str) -> dict[str, str]:
    """Returns git repository information for the given path."""
    try:
        p = Path(path).resolve()
        # Check if inside repo
        root_res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=p,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
        if root_res.returncode != 0:
            return {"is_git": False, "repo_name": "", "branch": "", "status": ""}

        repo_root = Path(root_res.stdout.strip())
        repo_name = repo_root.name

        # Get branch
        branch_res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=p,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
        branch = branch_res.stdout.strip()
        if not branch:
            # Might be detached HEAD
            head_res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=p,
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            branch = head_res.stdout.strip() or "HEAD"

        # Check if working directory is dirty
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=p,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
        dirty = bool(status_res.stdout.strip())

        return {
            "is_git": True,
            "repo_name": repo_name,
            "branch": branch,
            "dirty": dirty,
            "status": "● zmodyfikowane" if dirty else "✓ czyste",
        }
    except Exception:
        return {"is_git": False, "repo_name": "", "branch": "", "status": ""}
