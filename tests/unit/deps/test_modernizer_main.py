"""Public behavior tests for the pyproject modernizer."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraPyprojectModernizer
from tests import c, t, u


class TestFlextInfraPyprojectModernizer:
    """Validate only public modernizer behavior."""

    @staticmethod
    def _args(**overrides: t.Infra.InfraValue) -> argparse.Namespace:
        defaults: t.MutableContainerMapping = {
            "project": None,
            "dry_run": False,
            "verbose": False,
            "audit": False,
            "skip_comments": False,
            "skip_check": True,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_initialization_uses_explicit_workspace(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(workspace_root=modernizer_workspace)
        tm.that(modernizer.root, eq=modernizer_workspace)

    def test_find_pyproject_files_skips_venv_and_filters_projects(
        self,
        modernizer_workspace_with_projects: Path,
    ) -> None:
        ignored_venv = modernizer_workspace_with_projects / ".venv"
        ignored_venv.mkdir(exist_ok=True)
        (ignored_venv / c.Infra.Files.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "ignored-venv"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace_with_projects,
        )
        all_files = modernizer.find_pyproject_files()
        selected_files = modernizer.find_pyproject_files(
            project_paths=[modernizer_workspace_with_projects / "selected"],
        )
        tm.that(
            all(".venv" not in str(path) for path in all_files),
            eq=True,
        )
        tm.that(
            selected_files,
            eq=[
                modernizer_workspace_with_projects
                / "selected"
                / c.Infra.Files.PYPROJECT_FILENAME,
            ],
        )

    def test_process_file_returns_invalid_toml(
        self,
        modernizer_workspace: Path,
    ) -> None:
        pyproject = modernizer_workspace / c.Infra.Files.PYPROJECT_FILENAME
        pyproject.write_text("invalid [[[", encoding="utf-8")
        changes = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
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
        modernizer = FlextInfraPyprojectModernizer(workspace_root=modernizer_workspace)
        exit_code = modernizer.run(
            self._args(skip_comments=True, skip_check=True),
            u.Infra.CliArgs(workspace=modernizer_workspace, apply=True),
        )
        tm.that(exit_code, eq=0)
        tm.that(
            (modernizer_workspace / c.Infra.Files.PYPROJECT_FILENAME).read_text(
                encoding="utf-8"
            ),
            has='build-backend = "hatchling.build"',
        )

    def test_run_rejects_unknown_selected_project(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(workspace_root=modernizer_workspace)
        tm.that(
            modernizer.run(
                self._args(),
                u.Infra.CliArgs(
                    workspace=modernizer_workspace,
                    projects=["missing-project"],
                ),
            ),
            eq=2,
        )

    @pytest.mark.parametrize(
        "entrypoint",
        [
            FlextInfraPyprojectModernizer.run_cli,
            FlextInfraPyprojectModernizer.main,
        ],
    )
    def test_cli_entrypoints_report_pending_changes_in_audit_mode(
        self,
        modernizer_workspace: Path,
        entrypoint: Callable[[t.StrSequence | None], int],
    ) -> None:
        tm.that(
            entrypoint(
                [
                    "--workspace",
                    str(modernizer_workspace),
                    "--audit",
                    "--skip-comments",
                ],
            ),
            eq=1,
        )
