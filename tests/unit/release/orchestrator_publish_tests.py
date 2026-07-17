"""Public release publish-phase behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests import TestsFlextInfraUtilities as u, c

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReleasePublish:
    """Behavior contract for the public release publish phase."""

    class TestsDryRun:
        """Dry-run publish behavior."""

        @staticmethod
        def test_publish_dry_run_writes_notes_only(tmp_path: Path) -> None:
            """Write notes without changing docs or Git refs."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, initialize_root_git=True
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
                "--dry-run",
            )

            notes_path = (
                u.Tests.release_report_dir(workspace, c.Tests.RELEASE_VERSION_TARGET)
                / c.Tests.RELEASE_NOTES_FILENAME
            )
            tm.that(result, eq=0)
            tm.that(notes_path.is_file(), eq=True)
            tm.that((workspace / "docs" / "CHANGELOG.md").exists(), eq=False)
            tm.that(
                u.Cli.capture(
                    [c.Infra.GIT, "tag", "-l", c.Tests.RELEASE_TAG_TARGET],
                    cwd=workspace,
                ).unwrap(),
                eq="",
            )

    class TestsApply:
        """Applied publish behavior."""

        @staticmethod
        def test_publish_apply_updates_docs_and_creates_tag(tmp_path: Path) -> None:
            """Persist release documents and the exact annotated tag."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, initialize_root_git=True
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
            tm.that((workspace / "docs" / "releases" / "latest.md").is_file(), eq=True)
            tm.that(
                (
                    workspace / "docs" / "releases" / f"{c.Tests.RELEASE_TAG_TARGET}.md"
                ).is_file(),
                eq=True,
            )
            tm.that(
                u.Cli.capture(
                    [c.Infra.GIT, "tag", "-l", c.Tests.RELEASE_TAG_TARGET],
                    cwd=workspace,
                ).unwrap(),
                eq=c.Tests.RELEASE_TAG_TARGET,
            )

        @staticmethod
        def test_publish_push_without_origin_fails_after_local_tagging(
            tmp_path: Path,
        ) -> None:
            """Report push failure while retaining observable local publication."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, initialize_root_git=True
            )

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

            tm.that(result, eq=1)
            tm.that((workspace / "docs" / "CHANGELOG.md").is_file(), eq=True)
            tm.that(
                u.Cli.capture(
                    [c.Infra.GIT, "tag", "-l", c.Tests.RELEASE_TAG_TARGET],
                    cwd=workspace,
                ).unwrap(),
                eq=c.Tests.RELEASE_TAG_TARGET,
            )

    class TestsSelection:
        """Publish project-selection behavior."""

        @staticmethod
        def test_notes_include_only_selected_projects(tmp_path: Path) -> None:
            """Render root and selected projects without an unselected peer."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=("flext-a", "flext-b"), initialize_root_git=True
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_PUBLISH,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--tag",
                c.Tests.RELEASE_TAG_TARGET,
                "--projects",
                "flext-a",
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--dry-run",
            )

            notes_path = (
                u.Tests.release_report_dir(workspace, c.Tests.RELEASE_VERSION_TARGET)
                / c.Tests.RELEASE_NOTES_FILENAME
            )
            notes = notes_path.read_text(encoding="utf-8")
            tm.that(result, eq=0)
            tm.that(notes, has="- root")
            tm.that(notes, has="- flext-a")
            tm.that(notes, lacks="- flext-b")
