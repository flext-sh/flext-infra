"""Contract tests for the Go runtime required by go: backend selectors."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsToolchainGoBackend:
    """The independent Go runtime follows the moving fleet selector."""

    def test_go_version_tracks_latest_without_coupling_to_beads(self) -> None:
        """Keep Go policy explicit while mise.lock owns its exact release."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.go_version, eq="latest")


__all__: tuple[str, ...] = ()
