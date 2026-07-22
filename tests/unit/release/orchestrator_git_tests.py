"""Public release tests covering real Git effects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests import TestsFlextInfraUtilities as u, c

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReleaseGit:
    """Behavior contract for observable release Git effects."""

    class TestsBranches:
        """Release-branch behavior."""

        @staticmethod
        def test_cli_creates_branches_for_root_and_selected_project(
            tmp_path: Path,
        ) -> None:
            """Create release branches only in selected real repositories."""
            workspace = u.Tests.create_release_workspace(
                tmp_path,
                project_names=("flext-a", "flext-b"),
                initialize_root_git=True,
                initialize_project_git=True,
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VALIDATE,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                "flext-a",
                "--interactive",
                "0",
                "--create-branches",
                "1",
                "--apply",
            )

            release_ref = f"refs/heads/release/{c.Tests.RELEASE_VERSION_TARGET}"
            tm.that(result, eq=0)
            tm.that(u.Tests.git_ref_exists(workspace, release_ref), eq=True)
            tm.that(u.Tests.git_ref_exists(workspace / "flext-a", release_ref), eq=True)
            tm.that(
                u.Tests.git_ref_exists(workspace / "flext-b", release_ref), eq=False
            )

    class TestsTags:
        """Release-tag behavior."""

        @staticmethod
        def test_publish_succeeds_when_tag_already_exists(tmp_path: Path) -> None:
            """Treat an existing exact annotated release tag as idempotent."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, initialize_root_git=True
            )
            tm.ok(
                u.Cli.run_checked(
                    [
                        c.Infra.GIT,
                        "tag",
                        "-a",
                        c.Tests.RELEASE_TAG_TARGET,
                        "-m",
                        f"release: {c.Tests.RELEASE_TAG_TARGET}",
                    ],
                    cwd=workspace,
                )
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_PUBLISH,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--tag",
                c.Tests.RELEASE_TAG_TARGET,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that((workspace / "docs" / "CHANGELOG.md").is_file(), eq=True)
            tm.that(
                u.Cli.capture(
                    [c.Infra.GIT, "tag", "-l", c.Tests.RELEASE_TAG_TARGET],
                    cwd=workspace,
                ).unwrap(),
                eq=c.Tests.RELEASE_TAG_TARGET,
            )

    class TestsPush:
        """Release-push behavior."""

        @staticmethod
        def test_publish_push_succeeds_with_local_origin(tmp_path: Path) -> None:
            """Push the current branch and tag to a real local bare origin."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, initialize_root_git=True
            )
            u.Tests.configure_local_origin(workspace, tmp_path / "remote")

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_PUBLISH,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--tag",
                c.Tests.RELEASE_TAG_TARGET,
                "--push",
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that(
                u.Cli.capture(
                    [c.Infra.GIT, "tag", "-l", c.Tests.RELEASE_TAG_TARGET],
                    cwd=workspace,
                ).unwrap(),
                eq=c.Tests.RELEASE_TAG_TARGET,
            )
