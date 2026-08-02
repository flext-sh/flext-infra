"""Public release version transaction idempotence contract."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_tests import tm
from tests import TestsFlextInfraUtilities as u, c

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration]


class TestsReleaseVersionTransaction:
    """Prove an already-aligned release version is a successful fixed point."""

    def test_public_version_route_succeeds_twice_without_second_delta(
        self, tmp_path: Path
    ) -> None:
        """Keep source bytes and Git status stable on the second public run."""
        workspace = u.Tests.create_release_workspace(tmp_path)
        pyproject = workspace / "pyproject.toml"
        baseline_bytes = pyproject.read_bytes()

        first_exit = u.Tests.run_release_main(
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
        first_bytes = pyproject.read_bytes()
        first_status = tm.ok(
            u.Infra.git_capture_bytes(workspace, ("status", "--porcelain=v1", "-z"))
        )

        second_exit = u.Tests.run_release_main(
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

        tm.that(first_exit, eq=0)
        tm.that(first_bytes, ne=baseline_bytes)
        tm.that(
            first_bytes.decode(), has=f'version = "{c.Tests.RELEASE_VERSION_TARGET}"'
        )
        tm.that(second_exit, eq=0)
        tm.that(pyproject.read_bytes(), eq=first_bytes)
        tm.that(
            tm.ok(
                u.Infra.git_capture_bytes(workspace, ("status", "--porcelain=v1", "-z"))
            ),
            eq=first_status,
        )
