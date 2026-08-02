"""Tests for the manual-command blocker (AGENTS.md §5).

``command_blocked`` flags bare tool invocations that bypass make / flext_infra and
allows monopoly-routed commands. The generated pre-commit surface is validated
through the same typed Make workflow consumed by production.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t

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
                "uv run --all-packages python -m flext_infra check --what boundary"
            ),
            eq=False,
        )

    def test_path_prefixed_tool_blocked(self) -> None:
        tm.that(_V.command_blocked("/usr/bin/ruff check src/"), eq=True)

    def test_git_status_allowed(self) -> None:
        tm.that(_V.command_blocked("git status"), eq=False)

    def test_make_allowed(self) -> None:
        tm.that(_V.command_blocked("make check CHECK_GATES=lint"), eq=False)

    def test_flext_infra_allowed(self) -> None:
        tm.that(
            _V.command_blocked("python -m flext_infra check --what boundary"), eq=False
        )

    def test_pre_commit_sequence_uses_only_canonical_make_verbs(self) -> None:
        steps = tuple(
            step
            for step in config.Infra.codegen.make.workflow
            if "pre_commit" in step.contexts
        )

        tm.that(
            tuple(step.verb for step in steps),
            eq=("setup", "fix", "fmt", "check", "test"),
        )
        tm.that(
            tuple(step.apply for step in steps), eq=(False, True, True, False, False)
        )


__all__: t.StrSequence = []
