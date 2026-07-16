"""Public behavior tests for FlextInfraWorkspaceChecker.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from tests import c, p, t, u


class TestWorkspaceChecker:
    """Declarative public-contract tests for workspace checker setup."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("--fix --unsafe-fixes", ["--fix", "--unsafe-fixes"]), (None, []), ("", [])],
    )
    def test_parse_tool_args(self, raw: str | None, expected: t.StrSequence) -> None:
        tm.that(FlextInfraWorkspaceChecker.parse_tool_args(raw), eq=list(expected))

    def test_init_creates_default_reports_dir(self, tmp_path: Path) -> None:
        FlextInfraWorkspaceChecker(workspace=tmp_path)
        reports_dir = tmp_path / c.Infra.REPORTS_DIR_NAME / c.Infra.VERB_CHECK
        tm.that(reports_dir.is_dir(), eq=True)

    def test_execute_returns_failure(self, tmp_path: Path) -> None:
        result = FlextInfraWorkspaceChecker(workspace=tmp_path).execute()
        tm.fail(result, has="Use execute_command() directly")

    def test_resolve_gates_maps_type_alias_and_deduplicates(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates([
            c.Infra.TYPE_ALIAS,
            c.Infra.PYREFLY,
            c.Infra.LINT,
            c.Infra.LINT,
        ])
        tm.ok(result)
        tm.that(result.value, eq=[c.Infra.PYREFLY, c.Infra.LINT])

    def test_resolve_gates_rejects_unknown_gate(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["unknown"])
        tm.fail(result, has="unknown gate")

    def test_resolve_workspace_root_or_cwd_returns_absolute_path(self) -> None:
        tm.that(u.Infra.resolve_workspace_root_or_cwd(None).is_absolute(), eq=True)

    def test_run_projects_fails_when_reports_dir_is_not_a_directory(
        self, tmp_path: Path
    ) -> None:
        reports_file = tmp_path / "reports.txt"
        reports_file.write_text("", encoding="utf-8")

        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["project-a"], [c.Infra.LINT], reports_dir=reports_file
        )

        tm.fail(result)


__all__: t.StrSequence = []
