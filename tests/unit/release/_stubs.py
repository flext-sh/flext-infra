"""Shared stubs and fixtures for release orchestrator tests.

Provides fake service classes and workspace creation helpers using
real, lightweight test doubles.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from pathlib import Path
from types import SimpleNamespace

import pytest

from flext_infra import r
from tests.models import m
from tests.protocols import p
from tests.typings import t


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    """Create workspace root with pyproject.toml for release tests."""
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "Makefile").touch()
    (root / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    return root


class FakeUtilsNamespace:
    """Fake for the `u` namespace used in orchestrator module."""

    class Infra:
        """Fake Infra utilities namespace."""

        _git_checkout_result: p.Result[bool] = r[bool].ok(True)
        _git_run_result: p.Result[str] = r[str].ok("")
        _git_run_checked_result: p.Result[bool] = r[bool].ok(True)
        _git_tag_exists_result: p.Result[bool] = r[bool].ok(False)
        _git_create_tag_result: p.Result[bool] = r[bool].ok(True)
        _git_checkout_side_effects: Sequence[r[bool]] | None = None
        _call_count: int = 0

        @classmethod
        def git_checkout(cls, *args: str, **kwargs: str) -> p.Result[bool]:
            if cls._git_checkout_side_effects is not None:
                idx = cls._call_count
                cls._call_count += 1
                return cls._git_checkout_side_effects[idx]
            return cls._git_checkout_result

        @classmethod
        def git_run(cls, *args: str, **kwargs: str) -> p.Result[str]:
            return cls._git_run_result

        @classmethod
        def git_run_checked(cls, *args: str, **kwargs: str) -> p.Result[bool]:
            return cls._git_run_checked_result

        @classmethod
        def git_tag_exists(cls, *args: str, **kwargs: str) -> p.Result[bool]:
            return cls._git_tag_exists_result

        @classmethod
        def git_create_tag(cls, *args: str, **kwargs: str) -> p.Result[bool]:
            return cls._git_create_tag_result

        @classmethod
        def resolve_projects(
            cls,
            workspace_root: Path,
            names: t.StrSequence,
        ) -> p.Result[Sequence[SimpleNamespace]]:
            return r[Sequence[SimpleNamespace]].ok([])

        @classmethod
        def generate_notes(
            cls,
            version: str,
            tag: str,
            projects: Sequence[SimpleNamespace],
            changes: str,
            output_path: Path,
        ) -> p.Result[bool]:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(f"# Release {tag}\n{changes}\n", encoding="utf-8")
            return r[bool].ok(True)

        @classmethod
        def reset(cls) -> None:
            cls._git_checkout_result = r[bool].ok(True)
            cls._git_run_result = r[str].ok("")
            cls._git_run_checked_result = r[bool].ok(True)
            cls._git_tag_exists_result = r[bool].ok(False)
            cls._git_create_tag_result = r[bool].ok(True)
            cls._git_checkout_side_effects = None
            cls._call_count = 0


class FakeVersioning:
    """Fake for FlextInfraUtilitiesVersioning."""

    _parse_result: p.Result[str] = r[str].ok("1.0.0")
    _bump_result: p.Result[str] = r[str].ok("1.1.0")
    _replace_called: bool = False

    def parse_semver(self, *args: str, **kwargs: str) -> p.Result[str]:
        return self._parse_result

    def bump_version(self, *args: str, **kwargs: str) -> p.Result[str]:
        return self._bump_result

    def replace_project_version(self, *args: str, **kwargs: str) -> None:
        self._replace_called = True


class FakeSubprocess:
    """Fake command runner for CLI runtime execution."""

    _run_checked_result: p.Result[bool] = r[bool].ok(True)
    _run_raw_result: p.Result[m.Cli.CommandOutput] | None = None
    _run_checked_called: bool = False

    def run_checked(self, *args: str, **kwargs: str) -> p.Result[bool]:
        self._run_checked_called = True
        return self._run_checked_result

    def run_raw(self, *args: str, **kwargs: str) -> p.Result[m.Cli.CommandOutput]:
        if self._run_raw_result is not None:
            return self._run_raw_result
        output = m.Cli.CommandOutput(exit_code=0, stdout="ok", stderr="")
        return r[m.Cli.CommandOutput].ok(output)


class FakeReporting:
    """Fake for FlextInfraUtilitiesReporting."""

    _report_dir: Path | None = None

    def resolve_report_dir(self, *args: str, **kwargs: str) -> Path:
        if self._report_dir is not None:
            return self._report_dir
        msg = "report_dir not set on FakeReporting"
        raise ValueError(msg)


class FakeSelection:
    """Fake for FlextInfraUtilitiesSelection."""

    _resolve_result: p.Result[Sequence[m.Infra.ProjectInfo]] = r[
        Sequence[m.Infra.ProjectInfo]
    ].ok([])

    def resolve_projects(
        self,
        workspace_root: Path,
        names: t.StrSequence,
    ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
        return self._resolve_result


__all__: list[str] = [
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
    "workspace_root",
]
