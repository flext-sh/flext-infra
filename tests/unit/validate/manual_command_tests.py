"""Tests for the manual-command blocker (AGENTS.md §5).

``command_blocked`` flags bare tool invocations that bypass make / flext_infra and
allows monopoly-routed commands; ``render_pre_commit_config`` emits hooks that
call ``python -m flext_infra`` (never the retired audit scripts).
"""

from __future__ import annotations

from flext_tests import tm

from tests.typings import t
from flext_infra.validate.manual_command import FlextInfraManualCommandValidator

_V = FlextInfraManualCommandValidator


class TestManualCommandValidator:
    def test_bare_ruff_blocked(self) -> None:
        tm.that(_V.command_blocked("ruff check src/"), eq=True)

    def test_bare_pytest_blocked(self) -> None:
        tm.that(_V.command_blocked("pytest -q tests/"), eq=True)

    def test_git_commit_blocked(self) -> None:
        tm.that(_V.command_blocked("git commit -am wip"), eq=True)

    def test_sed_inplace_blocked(self) -> None:
        tm.that(_V.command_blocked("sed -i s/a/b/ file.py"), eq=True)

    def test_sed_inplace_suffix_blocked(self) -> None:
        tm.that(_V.command_blocked("sed -i.bak s/a/b/ file.py"), eq=True)

    def test_shell_composition_bypass_blocked(self) -> None:
        tm.that(_V.command_blocked("make x && ruff check"), eq=True)
        tm.that(_V.command_blocked("echo ok; ruff check src/"), eq=True)

    def test_wrapper_bypass_blocked(self) -> None:
        tm.that(_V.command_blocked("env ruff check"), eq=True)
        tm.that(_V.command_blocked("xargs pytest"), eq=True)

    def test_python_m_blocked_module_blocked(self) -> None:
        tm.that(_V.command_blocked("python -m ruff check"), eq=True)

    def test_uv_run_blocked_tool_blocked(self) -> None:
        for tool in ("ruff", "pytest", "mypy", "pyright"):
            tm.that(_V.command_blocked(f"uv run --all-packages {tool} src/"), eq=True)

    def test_uv_run_python_m_blocked_module_blocked(self) -> None:
        tm.that(_V.command_blocked("uv run --all-packages python -m pytest"), eq=True)

    def test_uv_run_flext_infra_allowed(self) -> None:
        tm.that(
            _V.command_blocked(
                "uv run --all-packages python -m flext_infra check --what boundary",
            ),
            eq=False,
        )

    def test_path_prefixed_tool_blocked(self) -> None:
        tm.that(_V.command_blocked("/usr/bin/ruff check src/"), eq=True)

    def test_git_status_allowed(self) -> None:
        tm.that(_V.command_blocked("git status"), eq=False)

    def test_make_allowed(self) -> None:
        tm.that(_V.command_blocked("make check WHAT=lint"), eq=False)

    def test_flext_infra_allowed(self) -> None:
        tm.that(
            _V.command_blocked("python -m flext_infra check --what boundary"),
            eq=False,
        )

    def test_render_uses_flext_infra_and_drops_scripts(self) -> None:
        rendered = _V.render_pre_commit_config()
        tm.that("python -m flext_infra check --what boundary" in rendered, eq=True)
        tm.that("audit_banned_cli_libs.py" not in rendered, eq=True)


__all__: t.StrSequence = []
