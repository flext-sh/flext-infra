"""Contract tests for the governed beads distribution pinned by the SSOT."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm

_GOVERNED_REPOSITORY = "marlon-costa-dc/beads"


class TestsToolchainBeadsDistribution:
    """beads installs from the governed fork, never from an upstream module.

    The upstream module path resolves to a distribution this workspace does not
    control: it lags the ledger schema the projects run, and it cannot receive
    fix-forward changes. The governed fork publishes release assets, so the
    selector consumes them through mise's github backend.
    """

    def test_selector_targets_the_governed_fork(self) -> None:
        """The pin names the governed fork through the github backend."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.selector, eq=f"github:{_GOVERNED_REPOSITORY}")

    def test_selector_never_targets_an_upstream_module(self) -> None:
        """No upstream owner may reappear in the selector."""
        selector = config.Infra.codegen.toolchain.beads.selector

        for upstream in ("steveyegge", "gastownhall"):
            tm.that(upstream in selector, eq=False)

    def test_version_is_the_governed_release_tag(self) -> None:
        """The installed version is the fork's published release tag."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.version, eq="1.1.2-dc1")

    def test_reported_version_matches_the_installed_binary(self) -> None:
        """`bd version` self-reports the same version the selector installs.

        The upstream module reported 1.1.0 while installing a later commit, so
        the preflight gate compared two different identities. The fork builds
        its own tag, so both are the same string.
        """
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.reported_version, eq=toolchain.beads.version)


__all__: tuple[str, ...] = ()
