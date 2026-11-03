import pytest
from pathlib import Path
from clicode.app import CliCodeApp
from clicode.core.git import get_git_info
from clicode.core.diagnostics import run_diagnostics
from clicode.core.runner import detect_run_commands, RunCommand
from clicode.ui.bottom_panel import BottomPanel
from clicode.ui.editor import CodeEditor
from clicode.ui.modals import LanguagePickerModal, RunPickerModal, BottomPanelPickerModal


def test_git_info():
    info = get_git_info(Path.cwd())
    assert info["is_git"] is True
    assert "repo_name" in info
    assert "branch" in info


def test_diagnostics_python_syntax_error():
    broken_code = "def foo(\n    print('unclosed')\n"
    diags = run_diagnostics(None, broken_code, "python")
    assert len(diags) > 0
    assert diags[0].severity == "error"


def test_diagnostics_python_clean():
    clean_code = "def foo():\n    return 42\n"
    diags = run_diagnostics(None, clean_code, "python")
    assert len(diags) == 0


def test_detect_run_commands():
    cmds = detect_run_commands(Path.cwd())
    assert len(cmds) > 0


@pytest.mark.asyncio
async def test_app_lifecycle_and_modals():
    app = CliCodeApp(target_dir=Path.cwd())
    async with app.run_test() as pilot:
        await pilot.pause()
        top_bar = app.query_one("#top-bar")
        assert top_bar is not None
        sidebar = app.query_one("#sidebar")
        assert sidebar is not None
        bottom = app.query_one("#bottom-panel", BottomPanel)
        assert bottom is not None
        editor = app.query_one("#editor", CodeEditor)
        assert editor is not None

        # Test Space + l (Language Modal)
        app.action_select_language()
        await pilot.pause()
        assert isinstance(app.screen, LanguagePickerModal)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, LanguagePickerModal)

        # Test Space + r (Run Modal)
        app.action_run_project()
        await pilot.pause()
        assert isinstance(app.screen, RunPickerModal)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, RunPickerModal)

        # Test Space + t (Bottom Panel Modal)
        app.action_select_bottom_panel()
        await pilot.pause()
        assert isinstance(app.screen, BottomPanelPickerModal)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, BottomPanelPickerModal)

        # Test switching tabs in bottom panel
        bottom.switch_tab("output")
        await pilot.pause()
        bottom.switch_tab("terminal")
        await pilot.pause()
        bottom.switch_tab("problems")
        await pilot.pause()
