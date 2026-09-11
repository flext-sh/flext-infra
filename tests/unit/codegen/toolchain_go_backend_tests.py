"""Contract tests for the Go runtime required by go: backend selectors."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsToolchainGoBackend:
    """The independent Go runtime follows one compatible release line."""

    def test_go_version_is_a_compatible_release_line(self) -> None:
        """Keep Go policy explicit without coupling it to the Beads backend."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.go_version, has=".")
        tm.that(
            all(part.isdecimal() for part in toolchain.go_version.split(".")), eq=True
        )


__all__: tuple[str, ...] = ()
