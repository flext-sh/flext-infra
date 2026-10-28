"""Tests for the manual-command blocker (AGENTS.md §5).

``command_blocked`` flags bare tool invocations that bypass make / flext_infra and
allows monopoly-routed commands. The former pre-commit-config drift half is
retired: the template owns the content and ``codegen conform --mode check``
owns drift detection, so no second detector may exist.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
from tests import tm

_V = FlextInfraManualCommandValidator


class TestsFlextInfraManualCommand:
    """Tests for ``FlextInfraManualCommand``."""

    @staticmethod
    def test_bare_ruff_blocked() -> None:
        """Test bare ruff blocked."""
        tm.ok(_V.command_blocked("ruff check src/"))

    @staticmethod
    def test_bare_pytest_blocked() -> None:
        """Test bare pytest blocked."""
        tm.ok(_V.command_blocked("pytest -q tests/"))

    @staticmethod
    def test_git_commit_blocked() -> None:
        """Test git commit blocked."""
        tm.ok(_V.command_blocked("git commit -am wip"))

    @staticmethod
    def test_sed_inplace_blocked() -> None:
        """Test sed inplace blocked."""
        tm.ok(_V.command_blocked("sed -i s/a/b/ file.py"))

    @staticmethod
    def test_sed_inplace_suffix_blocked() -> None:
        """Test sed inplace suffix blocked."""
        tm.ok(_V.command_blocked("sed -i.bak s/a/b/ file.py"))

    @staticmethod
    def test_shell_composition_bypass_blocked() -> None:
        """Test shell composition bypass blocked."""
        tm.ok(_V.command_blocked("make x && ruff check"))
        tm.ok(_V.command_blocked("echo ok; ruff check src/"))

    @staticmethod
    def test_wrapper_bypass_blocked() -> None:
        """Test wrapper bypass blocked."""
        tm.ok(_V.command_blocked("env ruff check"))
        tm.ok(_V.command_blocked("xargs pytest"))

    @staticmethod
    def test_python_m_blocked_module_blocked() -> None:
        """Test python m blocked module blocked."""
        tm.ok(_V.command_blocked("python -m ruff check"))

    @staticmethod
    def test_uv_run_blocked_tool_blocked() -> None:
        """Test uv run blocked tool blocked."""
        for tool in ("ruff", "pytest", "mypy", "pyright"):
            tm.ok(_V.command_blocked(f"uv run --all-packages {tool} src/"))

    @staticmethod
    def test_uv_run_python_m_blocked_module_blocked() -> None:
        """Test uv run python m blocked module blocked."""
        tm.ok(_V.command_blocked("uv run --all-packages python -m pytest"))

    @staticmethod
    def test_uv_run_flext_infra_allowed() -> None:
        """Test uv run flext infra allowed."""
        tm.that(
            _V.command_blocked(
                "uv run --all-packages python -m flext_infra check --what boundary",
            ),
            eq=False,
        )

    @staticmethod
    def test_path_prefixed_tool_blocked() -> None:
        """Test path prefixed tool blocked."""
        tm.ok(_V.command_blocked("/usr/bin/ruff check src/"))

    @staticmethod
    def test_git_status_allowed() -> None:
        """Test git status allowed."""
        tm.fail(_V.command_blocked("git status"))

    @staticmethod
    def test_make_allowed() -> None:
        """Test make allowed."""
        tm.fail(_V.command_blocked("make check"))

    @staticmethod
    def test_flext_infra_allowed() -> None:
        """Test flext infra allowed."""
        tm.that(
            _V.command_blocked("python -m flext_infra check --what boundary"),
            eq=False,
        )
