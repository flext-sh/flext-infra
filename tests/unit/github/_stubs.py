"""Lightweight test doubles for github test modules.

Replaces generic mock objects with typed, configurable stub classes
that satisfy flext_infra protocol contracts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import Annotated, ClassVar, override

from pydantic import Field
from tests import (
    m,
    r,
    t,
    u,
)


class StubCommandOutput(m.ArbitraryTypesModel):
    """Stub command output matching p.Cli.CommandOutput protocol."""

    exit_code: Annotated[int, Field(default=0, description="Command exit code")] = 0
    stdout: Annotated[str, Field(default="", description="Captured stdout")] = ""
    stderr: Annotated[str, Field(default="", description="Captured stderr")] = ""


class StubRunner:
    """Configurable stub for p.Cli.CommandRunner protocol."""

    def __init__(
        self,
        run_returns: Sequence[r[m.Cli.CommandOutput]] | None = None,
        capture_returns: Sequence[r[str]] | None = None,
        run_checked_returns: Sequence[r[bool]] | None = None,
        run_to_file_returns: Sequence[r[int]] | None = None,
    ) -> None:
        self._run_returns: MutableSequence[r[m.Cli.CommandOutput]] = list(
            run_returns or []
        )
        self._capture_returns: MutableSequence[r[str]] = list(capture_returns or [])
        self._run_checked_returns: MutableSequence[r[bool]] = list(
            run_checked_returns or []
        )
        self._run_to_file_returns: MutableSequence[r[int]] = list(
            run_to_file_returns or []
        )
        self.run_calls: MutableSequence[t.StrSequence] = []
        self.capture_calls: MutableSequence[t.StrSequence] = []
        self.run_checked_calls: MutableSequence[t.StrSequence] = []
        self.run_to_file_calls: MutableSequence[t.StrSequence] = []

    @staticmethod
    def _pop_run(
        returns: MutableSequence[r[m.Cli.CommandOutput]],
    ) -> r[m.Cli.CommandOutput]:
        if not returns:
            return r[m.Cli.CommandOutput].fail("no return value configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    @staticmethod
    def _pop_capture(returns: MutableSequence[r[str]]) -> r[str]:
        if not returns:
            return r[str].fail("no return value configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    @staticmethod
    def _pop_checked(returns: MutableSequence[r[bool]]) -> r[bool]:
        if not returns:
            return r[bool].fail("no return value configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    @staticmethod
    def _pop_to_file(returns: MutableSequence[r[int]]) -> r[int]:
        if not returns:
            return r[int].fail("no return value configured")
        return returns[0] if len(returns) == 1 else returns.pop(0)

    def run(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[m.Cli.CommandOutput]:
        _ = cwd, timeout, env
        self.run_calls.append(list(cmd))
        return self._pop_run(self._run_returns)

    def capture(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[str]:
        _ = cwd, timeout, env
        self.capture_calls.append(list(cmd))
        return self._pop_capture(self._capture_returns)

    def run_checked(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[bool]:
        _ = cwd, timeout, env
        self.run_checked_calls.append(list(cmd))
        return self._pop_checked(self._run_checked_returns)

    def run_to_file(
        self,
        cmd: t.StrSequence,
        output_file: Path,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[int]:
        _ = output_file, cwd, timeout, env
        self.run_to_file_calls.append(list(cmd))
        return self._pop_to_file(self._run_to_file_returns)

    def run_raw(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[m.Cli.CommandOutput]:
        return self.run(cmd, cwd=cwd, timeout=timeout, env=env)


class StubJsonIo:
    """Stub for a JSON writer dependency."""

    json_write_returns: ClassVar[r[bool]] = r[bool].ok(True)
    json_write_calls: ClassVar[list[tuple[Path, t.Cli.JsonPayload]]] = []

    def __init__(self, write_returns: r[bool] | None = None) -> None:
        StubJsonIo.json_write_returns = write_returns or r[bool].ok(True)
        StubJsonIo.json_write_calls = []

    @staticmethod
    def json_write(
        path: Path,
        payload: t.Cli.JsonPayload,
        *,
        sort_keys: bool = False,
        ensure_ascii: bool = False,
        indent: int = 2,
    ) -> r[bool]:
        _ = sort_keys, ensure_ascii, indent
        StubJsonIo.json_write_calls.append((path, payload))
        return StubJsonIo.json_write_returns


class StubVersioning(u.Infra):
    """Stub for u.Infra."""

    _release_tag_returns: ClassVar[r[str]] = r[str].fail("no tag")

    def __init__(self, release_tag_returns: r[str] | None = None) -> None:
        StubVersioning._release_tag_returns = release_tag_returns or r[str].fail(
            "no tag",
        )

    @staticmethod
    def release_tag_from_branch(branch: str) -> r[str]:
        _ = branch
        return StubVersioning._release_tag_returns


class StubSelector(u.Infra):
    """Stub for u.Infra."""

    _resolve_returns: ClassVar[r[Sequence[m.Infra.ProjectInfo]]] = r[
        Sequence[m.Infra.ProjectInfo]
    ].ok([])

    def __init__(
        self,
        resolve_returns: r[Sequence[m.Infra.ProjectInfo]] | None = None,
    ) -> None:
        StubSelector._resolve_returns = (
            resolve_returns
            if resolve_returns is not None
            else r[Sequence[m.Infra.ProjectInfo]].ok([])
        )

    @staticmethod
    @override
    def resolve_projects(
        workspace_root: Path,
        names: t.StrSequence,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        _ = workspace_root, names
        return StubSelector._resolve_returns


class StubReporting(u.Infra):
    """Stub for u.Infra."""

    _report_dir: ClassVar[Path] = Path("/tmp/reports")

    def __init__(self, report_dir: Path | None = None) -> None:
        StubReporting._report_dir = report_dir or Path("/tmp/reports")

    @staticmethod
    @override
    def get_report_dir(
        workspace_root: Path | str,
        scope: str,
        verb: str,
    ) -> Path:
        _ = workspace_root, scope, verb
        return StubReporting._report_dir


class StubProjectInfo(m.Infra.ProjectInfo):
    """Stub for p.Infra.ProjectInfo protocol."""

    name: Annotated[str, Field(default="test-project", description="Project name")] = (
        "test-project"
    )
    path: Annotated[
        Path,
        Field(default=Path("/tmp/test-project"), description="Project path"),
    ] = Path("/tmp/test-project")
    stack: Annotated[
        str,
        Field(default="python", description="Primary technology stack"),
    ] = "python"
    has_tests: Annotated[
        bool,
        Field(default=False, description="Project has tests"),
    ] = False
    has_src: Annotated[bool, Field(default=True, description="Project has source")] = (
        True
    )


__all__ = [
    "StubCommandOutput",
    "StubJsonIo",
    "StubProjectInfo",
    "StubReporting",
    "StubRunner",
    "StubSelector",
    "StubVersioning",
]
