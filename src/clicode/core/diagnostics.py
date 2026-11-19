from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Diagnostic:
    file_path: str
    line: int
    column: int
    severity: str  # "error", "warning", "info"
    message: str
    source: str


def run_diagnostics(file_path: str | Path | None, content: str, language: str) -> list[Diagnostic]:
    """Runs diagnostics for the given file/code using installed tools."""
    diagnostics: list[Diagnostic] = []
    lang = (language or "").lower().strip()
    path_str = str(file_path) if file_path else ""

    # Prepare temporary file if not saved to disk
    temp_file: str | None = None
    target_path = path_str
    if not path_str or not os.path.exists(path_str):
        suffix = _get_suffix_for_lang(lang)
        fd, temp_file = tempfile.mkstemp(suffix=suffix, prefix="clicode_lint_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        target_path = temp_file

    try:
        if lang in ("python", "py"):
            diagnostics.extend(_check_python(target_path, content))
        elif lang in ("dart", "flutter"):
            diagnostics.extend(_check_dart(target_path))
        elif lang in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
            diagnostics.extend(_check_javascript(target_path, lang))
        elif lang in ("rust", "rs"):
            diagnostics.extend(_check_rust(target_path))
        elif lang in ("go", "golang"):
            diagnostics.extend(_check_go(target_path))
        elif lang in ("bash", "sh", "zsh", "shell"):
            diagnostics.extend(_check_bash(target_path))
        elif lang in ("c", "cpp", "c++"):
            diagnostics.extend(_check_c(target_path, lang))
        elif lang in ("json",):
            diagnostics.extend(_check_json(content))
        elif lang in ("yaml", "yml"):
            diagnostics.extend(_check_yaml(content))
        elif lang in ("toml",):
            diagnostics.extend(_check_toml(content))
        else:
            # Generic fallback based on extension
            if target_path.endswith(".dart"):
                diagnostics.extend(_check_dart(target_path))
            elif target_path.endswith(".py"):
                diagnostics.extend(_check_python(target_path, content))
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

    return diagnostics


def _get_suffix_for_lang(lang: str) -> str:
    mapping = {
        "python": ".py",
        "dart": ".dart",
        "flutter": ".dart",
        "javascript": ".js",
        "typescript": ".ts",
        "rust": ".rs",
        "go": ".go",
        "bash": ".sh",
        "c": ".c",
        "cpp": ".cpp",
        "json": ".json",
        "yaml": ".yaml",
        "toml": ".toml",
        "html": ".html",
        "css": ".css",
    }
    return mapping.get(lang, ".txt")


def _check_python(path: str, content: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    
    # 1. Python compilation check
    try:
        compile(content, path or "<buffer>", "exec")
    except SyntaxError as e:
        diags.append(
            Diagnostic(
                file_path=path,
                line=e.lineno or 1,
                column=e.offset or 1,
                severity="error",
                message=f"SyntaxError: {e.msg}",
                source="python",
            )
        )
        return diags
    except Exception as e:
        diags.append(
            Diagnostic(
                file_path=path,
                line=1,
                column=1,
                severity="error",
                message=str(e),
                source="python",
            )
        )
        return diags

    # 2. Check if flake8 / ruff is installed in system
    if shutil.which("ruff"):
        try:
            res = subprocess.run(
                ["ruff", "check", "--output-format=json", path],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.stdout:
                items = json.loads(res.stdout)
                for item in items:
                    diags.append(
                        Diagnostic(
                            file_path=path,
                            line=item.get("location", {}).get("row", 1),
                            column=item.get("location", {}).get("column", 1),
                            severity="warning",
                            message=f"{item.get('code')}: {item.get('message')}",
                            source="ruff",
                        )
                    )
        except Exception:
            pass
    elif shutil.which("flake8"):
        try:
            res = subprocess.run(
                ["flake8", "--format=%(row)d:%(col)d:%(code)s:%(text)s", path],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for line in res.stdout.splitlines():
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    diags.append(
                        Diagnostic(
                            file_path=path,
                            line=int(parts[0]),
                            column=int(parts[1]),
                            severity="warning",
                            message=f"{parts[2]}: {parts[3]}",
                            source="flake8",
                        )
                    )
        except Exception:
            pass

    return diags


def _check_dart(path: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    dart_bin = shutil.which("dart") or shutil.which("flutter")
    if not dart_bin:
        return diags

    try:
        # dart analyze --format=json path
        cmd = ["dart", "analyze", "--format=json", path]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = res.stdout
        if output.strip().startswith("{") and "diagnostics" in output:
            data = json.loads(output)
            for d in data.get("diagnostics", []):
                sev = d.get("severity", "INFO").lower()
                location = d.get("location", {})
                start = location.get("start", {})
                diags.append(
                    Diagnostic(
                        file_path=location.get("file", path),
                        line=start.get("line", 1),
                        column=start.get("column", 1),
                        severity="error" if sev == "error" else "warning",
                        message=d.get("problemMessage", ""),
                        source="dart",
                    )
                )
        else:
            # Parsowanie linii tekstowej: [error] Message (file:line:col)
            # lub line X col Y: message
            for line in output.splitlines():
                if "•" in line:
                    # np:   error • Undefined name 'xyz' • file.dart:5:3 • undefined_identifier
                    parts = [p.strip() for p in line.split("•")]
                    if len(parts) >= 3:
                        sev = "error" if "error" in parts[0].lower() else "warning"
                        msg = parts[1]
                        loc_part = parts[2]
                        # file.dart:line:col
                        match = re.search(r":(\d+):(\d+)", loc_part)
                        line_num = int(match.group(1)) if match else 1
                        col_num = int(match.group(2)) if match else 1
                        diags.append(
                            Diagnostic(
                                file_path=path,
                                line=line_num,
                                column=col_num,
                                severity=sev,
                                message=msg,
                                source="dart",
                            )
                        )
    except Exception:
        pass

    return diags


def _check_javascript(path: str, lang: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    if shutil.which("node") and lang in ("javascript", "js"):
        try:
            res = subprocess.run(
                ["node", "--check", path],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if res.returncode != 0:
                err = res.stderr
                line_match = re.search(r":(\d+)", err)
                line_num = int(line_match.group(1)) if line_match else 1
                msg = err.splitlines()[-1] if err.splitlines() else "JavaScript syntax error"
                diags.append(
                    Diagnostic(
                        file_path=path,
                        line=line_num,
                        column=1,
                        severity="error",
                        message=msg,
                        source="node",
                    )
                )
        except Exception:
            pass

    return diags


def _check_rust(path: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    if shutil.which("rustc"):
        try:
            res = subprocess.run(
                ["rustc", "--error-format=short", "-Zno-codegen", path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in res.stderr.splitlines():
                match = re.match(r"^.*?:(\d+):(\d+):\s*(error|warning):\s*(.*)$", line)
                if match:
                    diags.append(
                        Diagnostic(
                            file_path=path,
                            line=int(match.group(1)),
                            column=int(match.group(2)),
                            severity=match.group(3),
                            message=match.group(4),
                            source="rustc",
                        )
                    )
        except Exception:
            pass
    return diags


def _check_go(path: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    if shutil.which("go"):
        try:
            res = subprocess.run(
                ["go", "vet", path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in res.stderr.splitlines():
                match = re.search(r":(\d+):(\d+):\s*(.*)$", line)
                if match:
                    diags.append(
                        Diagnostic(
                            file_path=path,
                            line=int(match.group(1)),
                            column=int(match.group(2)),
                            severity="warning",
                            message=match.group(3),
                            source="go vet",
                        )
                    )
        except Exception:
            pass
    return diags


def _check_bash(path: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    if shutil.which("bash"):
        try:
            res = subprocess.run(
                ["bash", "-n", path],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for line in res.stderr.splitlines():
                match = re.search(r"line (\d+):\s*(.*)$", line)
                if match:
                    diags.append(
                        Diagnostic(
                            file_path=path,
                            line=int(match.group(1)),
                            column=1,
                            severity="error",
                            message=match.group(2),
                            source="bash",
                        )
                    )
        except Exception:
            pass
    return diags


def _check_c(path: str, lang: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler:
        try:
            res = subprocess.run(
                [compiler, "-fsyntax-only", path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in res.stderr.splitlines():
                match = re.match(r"^.*?:(\d+):(\d+):\s*(error|warning):\s*(.*)$", line)
                if match:
                    diags.append(
                        Diagnostic(
                            file_path=path,
                            line=int(match.group(1)),
                            column=int(match.group(2)),
                            severity=match.group(3),
                            message=match.group(4),
                            source=compiler,
                        )
                    )
        except Exception:
            pass
    return diags


def _check_json(content: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        diags.append(
            Diagnostic(
                file_path="",
                line=e.lineno,
                column=e.colno,
                severity="error",
                message=f"JSON Error: {e.msg}",
                source="json",
            )
        )
    return diags


def _check_yaml(content: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    try:
        import yaml  # type: ignore
        yaml.safe_load(content)
    except ImportError:
        pass
    except Exception as e:
        line = getattr(e, "problem_mark", None)
        l_num = line.line + 1 if line else 1
        c_num = line.column + 1 if line else 1
        diags.append(
            Diagnostic(
                file_path="",
                line=l_num,
                column=c_num,
                severity="error",
                message=str(e),
                source="yaml",
            )
        )
    return diags


def _check_toml(content: str) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    try:
        import tomllib  # Python 3.11+
        tomllib.loads(content)
    except Exception as e:
        diags.append(
            Diagnostic(
                file_path="",
                line=1,
                column=1,
                severity="error",
                message=f"TOML Error: {e}",
                source="toml",
            )
        )
    return diags
