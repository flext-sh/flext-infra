"""Public release CLI flow tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c
from tests import TestsFlextInfraUtilities as u
from flext_tests import tm

from pathlib import Path



class TestsFlextInfraReleaseFlow:
    """Behavior contract for complete public release CLI flows."""

    class TestsValidation:
        """Validation flow behavior."""

        @staticmethod
        def test_main_validate_apply_succeeds(tmp_path: Path) -> None:
            """Validate one selected committed project through the public CLI."""
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                project_names=(c.Tests.RELEASE_PROJECTS[0],),
                initialize_project_git=True,
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VALIDATE,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)

    class TestsVersioning:
        """Version flow behavior."""

        @staticmethod
        def test_main_version_apply_updates_root_and_selected_project(
            tmp_path: Path,
        ) -> None:
            """Update only the root and selected project through the public CLI."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=c.Tests.RELEASE_PROJECTS
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VERSION,
                "--version",
                c.Tests.RELEASE_VERSION_SELECTED,
                "--projects",
                c.Tests.RELEASE_PROJECTS[0],
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that(
                (workspace / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_SELECTED}"',
            )
            tm.that(
                (
                    workspace / c.Tests.RELEASE_PROJECTS[0] / "pyproject.toml"
                ).read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_SELECTED}"',
            )
            tm.that(
                (
                    workspace / c.Tests.RELEASE_PROJECTS[1] / "pyproject.toml"
                ).read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_BASE}"',
            )

    class TestsBuild:
        """Build flow behavior."""

        @staticmethod
        def test_main_build_with_bump_uses_resolved_report_version(
            tmp_path: Path,
        ) -> None:
            """Use the resolved bumped version as the build report directory."""
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                project_names=(c.Tests.RELEASE_PROJECTS[0],),
                initialize_project_git=True,
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--bump",
                c.Tests.RELEASE_BUMP_MINOR,
                "--projects",
                c.Tests.RELEASE_PROJECTS[0],
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that(
                (
                    u.Tests.release_report_dir(workspace, "0.2.0") / "build-report.json"
                ).is_file(),
                eq=True,
            )

    class TestsCompleteFlow:
        """Multi-phase flow behavior."""

        @staticmethod
        def test_main_all_dry_run_writes_release_artifacts(tmp_path: Path) -> None:
            """Write reports and notes without persisting package artifacts."""
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                project_names=(c.Tests.RELEASE_PROJECTS[0],),
                initialize_root_git=True,
                initialize_project_git=True,
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Infra.RELEASE_PHASE_ALL,
                "--interactive",
                "0",
                "--dry-run",
            )

            tm.that(result, eq=0)
            report_dir = u.Tests.release_report_dir(
                workspace, c.Tests.RELEASE_VERSION_BASE
            )
            tm.that((report_dir / "build-report.json").is_file(), eq=True)
            tm.that((report_dir / c.Tests.RELEASE_NOTES_FILENAME).is_file(), eq=True)

    class TestsInvalidInput:
        """Fail-closed input behavior."""

        @staticmethod
        def test_main_invalid_version_returns_failure(tmp_path: Path) -> None:
            """Return a public CLI failure for invalid release metadata."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VERSION,
                "--version",
                "invalid",
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=1)
