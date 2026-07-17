"""Public release version and tag resolution tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReleaseVersionResolution:
    """Behavior contract for public release identity resolution."""

    class TestsExplicitVersion:
        """Explicit version behavior."""

        @staticmethod
        def test_explicit_version_updates_workspace_file(tmp_path: Path) -> None:
            """Write an explicit release version to the workspace manifest."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VERSION,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that(
                (workspace / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_TARGET}"',
            )

        @staticmethod
        def test_dev_suffix_appends_development_version(tmp_path: Path) -> None:
            """Append the requested development suffix to the release version."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VERSION,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--dev-suffix",
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that(
                (workspace / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_TARGET}-dev"',
            )

    class TestsBump:
        """Semantic bump behavior."""

        @staticmethod
        def test_bump_uses_current_workspace_version(tmp_path: Path) -> None:
            """Resolve a bump from the current version before a real build."""
            project_name = c.Tests.RELEASE_PROJECTS[0]
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=(project_name,), initialize_project_git=True
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_BUILD,
                "--bump",
                c.Tests.RELEASE_BUMP_MINOR,
                "--projects",
                project_name,
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

    class TestsInvalidIdentity:
        """Fail-closed version and tag behavior."""

        @staticmethod
        def test_invalid_explicit_version_fails(tmp_path: Path) -> None:
            """Fail when the explicit version is not valid release metadata."""
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

        @staticmethod
        def test_invalid_tag_prefix_fails(tmp_path: Path) -> None:
            """Fail when the release tag omits its required prefix."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VERSION,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--tag",
                c.Tests.RELEASE_VERSION_TARGET,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=1)
