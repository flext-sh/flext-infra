"""Public release orchestration behavior tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from tests import TestsFlextInfraUtilities as u, c

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReleaseOrchestration:
    """Behavior contract for orchestration through the public CLI."""

    class TestsPhaseDispatch:
        """Phase selection and failure-order behavior."""

        @staticmethod
        def test_invalid_phase_fails(tmp_path: Path) -> None:
            """Reject an unknown phase at the public command boundary."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                "invalid",
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=1)

        @staticmethod
        def test_validate_failure_stops_before_version_update(tmp_path: Path) -> None:
            """Stop the public pipeline before a later version mutation."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, root_validate_exit_code="1"
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                f"{c.Tests.RELEASE_PHASE_VALIDATE} {c.Tests.RELEASE_PHASE_VERSION}",
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--interactive",
                "0",
                "--create-branches",
                "0",
                "--apply",
            )

            tm.that(result, eq=1)
            tm.that(
                (workspace / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_BASE}"',
            )

    class TestsProjectSelection:
        """Selected-project behavior."""

        @staticmethod
        def test_version_updates_only_selected_project(tmp_path: Path) -> None:
            """Update the root and selected project without touching its peer."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, project_names=("flext-a", "flext-b")
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VERSION,
                "--version",
                c.Tests.RELEASE_VERSION_TARGET,
                "--projects",
                "flext-a",
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
            tm.that(
                (workspace / "flext-a" / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_TARGET}"',
            )
            tm.that(
                (workspace / "flext-b" / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_BASE}"',
            )

    class TestsNextDevelopment:
        """Next-development version behavior."""

        @staticmethod
        def test_next_dev_updates_workspace_after_release(tmp_path: Path) -> None:
            """Apply the configured next development version after release."""
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
                "--next-dev",
                "--apply",
            )

            tm.that(result, eq=0)
            tm.that(
                (workspace / "pyproject.toml").read_text(),
                has=f'version = "{c.Tests.RELEASE_VERSION_NEXT_DEV}"',
            )
