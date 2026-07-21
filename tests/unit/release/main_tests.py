"""Public release CLI behavior tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main
from tests import c
from tests import TestsFlextInfraUtilities as u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReleaseCli:
    """Behavior contract for the public release command group."""

    class TestsHelp:
        """Public command-discovery behavior."""

        @staticmethod
        def test_release_group_help_returns_zero() -> None:
            """Expose the release command group through the public CLI."""
            tm.that(main(["release", "--help"]), eq=0)

        @staticmethod
        def test_release_run_subcommand_help_returns_zero() -> None:
            """Expose the release run options through the public CLI."""
            tm.that(main(["release", "run", "--help"]), eq=0)

    class TestsValidation:
        """Public validation-phase behavior."""

        @staticmethod
        def test_release_run_validate_dry_run_succeeds(tmp_path: Path) -> None:
            """Validate a real workspace without applying its Make gate."""
            workspace = u.Tests.create_release_workspace(tmp_path)

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VALIDATE,
                "--interactive",
                "0",
                "--dry-run",
            )

            tm.that(result, eq=0)

        @staticmethod
        def test_release_run_validate_apply_propagates_make_failure(
            tmp_path: Path,
        ) -> None:
            """Propagate a real workspace validation failure to the CLI exit."""
            workspace = u.Tests.create_release_workspace(
                tmp_path, root_validate_exit_code="1"
            )

            result = u.Tests.run_release_main(
                workspace,
                "--phase",
                c.Tests.RELEASE_PHASE_VALIDATE,
                "--interactive",
                "0",
                "--apply",
            )

            tm.that(result, eq=1)
