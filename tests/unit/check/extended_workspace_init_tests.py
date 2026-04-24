"""Public behavior tests for FlextInfraWorkspaceChecker."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraWorkspaceChecker
from tests import c, t, u


class TestWorkspaceChecker:
    """Declarative public-contract tests for workspace checker setup."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("--fix --unsafe-fixes", ["--fix", "--unsafe-fixes"]),
            (None, []),
            ("", []),
        ],
    )
    def test_parse_tool_args(
        self,
        raw: str | None,
        expected: t.StrSequence,
    ) -> None:
        tm.that(FlextInfraWorkspaceChecker.parse_tool_args(raw), eq=list(expected))

    def test_init_creates_default_reports_dir(self, tmp_path: Path) -> None:
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        tm.that(checker._default_reports_dir.exists(), eq=True)

    def test_execute_returns_failure(self, tmp_path: Path) -> None:
        result = FlextInfraWorkspaceChecker(workspace=tmp_path).execute()
        tm.fail(result, has="Use execute_command() directly")

    def test_resolve_gates_maps_type_alias_and_deduplicates(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(
            [c.Infra.TYPE_ALIAS, c.Infra.PYREFLY, c.Infra.LINT, c.Infra.LINT],
        )
        tm.ok(result)
        tm.that(result.value, eq=[c.Infra.PYREFLY, c.Infra.LINT])

    def test_resolve_gates_rejects_unknown_gate(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["unknown"])
        tm.fail(result, has="unknown gate")

    def test_resolve_workspace_root_or_cwd_returns_absolute_path(self) -> None:
        tm.that(u.Infra.resolve_workspace_root_or_cwd(None).is_absolute(), eq=True)

    def test_run_projects_fails_when_reports_dir_is_not_a_directory(
        self,
        tmp_path: Path,
    ) -> None:
        reports_file = tmp_path / "reports.txt"
        reports_file.write_text("", encoding="utf-8")

        result = FlextInfraWorkspaceChecker(workspace=tmp_path).run_projects(
            ["project-a"],
            [c.Infra.LINT],
            reports_dir=reports_file,
        )

        tm.fail(result)


__all__: t.StrSequence = []
