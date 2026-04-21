"""Edge-case tests for public modernizer flows."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraPyprojectModernizer
from tests import c


class TestFlextInfraPyprojectModernizerEdgeCases:
    """Validate edge cases through the public modernizer API."""

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            pytest.param(None, 2, id="missing-root-pyproject"),
            pytest.param("", 0, id="empty-root-pyproject"),
            pytest.param("[invalid toml {", 2, id="invalid-root-pyproject"),
        ],
    )
    def test_run_handles_root_edge_cases(
        self,
        tmp_path: Path,
        content: str | None,
        expected: int,
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        if content is not None:
            (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
                content,
                encoding="utf-8",
            )
        modernizer = FlextInfraPyprojectModernizer(workspace=workspace)
        tm.that(modernizer.run(), eq=expected)

    def test_audit_returns_zero_after_workspace_is_canonical(
        self,
        modernizer_workspace: Path,
    ) -> None:
        apply_exit = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            apply_changes=True,
            skip_comments=True,
            skip_check=True,
        ).run()
        audit_exit = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            audit=True,
            skip_comments=True,
        ).run()
        tm.that(apply_exit, eq=0)
        tm.that(audit_exit, eq=0)

    def test_run_fails_when_selected_project_has_invalid_toml(
        self,
        modernizer_workspace_with_projects: Path,
    ) -> None:
        selected_pyproject = (
            modernizer_workspace_with_projects / "selected" / c.Infra.PYPROJECT_FILENAME
        )
        selected_pyproject.write_text("[invalid", encoding="utf-8")
        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace_with_projects,
            apply_changes=True,
            skip_comments=True,
            skip_check=False,
        )
        tm.that(modernizer.run(), eq=1)
