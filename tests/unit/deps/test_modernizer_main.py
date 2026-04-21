"""Public behavior tests for the pyproject modernizer."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraPyprojectModernizer, main
from tests import c


class TestFlextInfraPyprojectModernizer:
    """Validate only public modernizer behavior."""

    def test_initialization_uses_explicit_workspace(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(workspace=modernizer_workspace)
        tm.that(modernizer.root, eq=modernizer_workspace)

    def test_process_file_returns_invalid_toml(
        self,
        modernizer_workspace: Path,
    ) -> None:
        pyproject = modernizer_workspace / c.Infra.PYPROJECT_FILENAME
        pyproject.write_text("invalid [[[", encoding="utf-8")
        changes = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
        ).process_file(
            pyproject,
            canonical_dev=[],
            dry_run=True,
            skip_comments=False,
        )
        tm.that(changes, has="invalid TOML")

    def test_run_apply_updates_root_pyproject(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            apply_changes=True,
            skip_comments=True,
            skip_check=True,
        )
        exit_code = modernizer.run()
        tm.that(exit_code, eq=0)
        tm.that(
            (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
                encoding="utf-8"
            ),
            has='build-backend = "hatchling.build"',
        )

    def test_run_rejects_unknown_selected_project(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            selected_projects=["missing-project"],
        )
        tm.that(modernizer.run(), eq=2)

    def test_cli_reports_pending_changes_in_audit_mode(
        self,
        modernizer_workspace: Path,
    ) -> None:
        tm.that(
            main([
                "deps",
                "modernize",
                "--workspace",
                str(modernizer_workspace),
                "--audit",
                "--skip-comments",
            ]),
            eq=1,
        )
