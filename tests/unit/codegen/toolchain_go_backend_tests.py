"""Contract tests for the Go runtime required by go: backend selectors."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsToolchainGoBackend:
    """A go: backend selector requires the Go runtime to be a declared tool.

    mise resolves backend selectors through a dependency graph: a ``go:`` tool
    is only installable when ``go`` itself is a declared tool. Without the
    declaration mise falls back to ``go`` on PATH, so every runner without an
    ambient Go toolchain (macOS, Windows, the distro-matrix images) fails with
    "go may be required but was not found".
    """

    def test_go_runtime_is_declared_when_beads_uses_the_go_backend(self) -> None:
        """The Go runtime is pinned whenever beads installs from a go: selector."""
        toolchain = config.Infra.codegen.toolchain

        if not toolchain.beads.selector.startswith("go:"):
            return

        tm.that(toolchain.go_version, empty=False)

    def test_go_version_is_an_exact_pin(self) -> None:
        """Every native toolchain floor pins an exact version, Go included."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.go_version, has=".")
        tm.that(toolchain.go_version.count("."), eq=2)

    def test_go_version_satisfies_the_pinned_beads_module(self) -> None:
        """Go is new enough to build the beads commit pinned in the SSOT.

        The beads go.mod at the pinned commit declares ``go 1.26.5``; a lower
        toolchain makes ``go install`` fetch another toolchain or fail outright.
        """
        toolchain = config.Infra.codegen.toolchain
        major, _, rest = toolchain.go_version.partition(".")
        minor, _, _patch = rest.partition(".")

        tm.that(int(major), eq=1)
        tm.that(int(minor), gte=26)


__all__: tuple[str, ...] = ()
