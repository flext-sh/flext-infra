"""Contract tests for the governed beads distribution pinned by the SSOT."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm

_GOVERNED_REPOSITORY = "gastownhall/beads"
_GOVERNED_VERSION = "1.2.2"
_GOVERNED_SCHEMA = 53
_LINUX_X64_SHA256 = "54fc0e0581ce4c5487a5b242f0a4f34af1ef09cf056e164a1af63a6ec7aa1e0e"


class TestsToolchainBeadsDistribution:
    """beads installs from the governed fork, never from an upstream module.

    The upstream module path resolves to a distribution this workspace does not
    control: it lags the ledger schema the projects run, and it cannot receive
    fix-forward changes. The governed fork publishes release assets, so the
    selector consumes them through mise's github backend.
    """

    def test_selector_targets_the_gas_city_distribution(self) -> None:
        """The pin names the governed fork through the github backend."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.selector, eq=f"github:{_GOVERNED_REPOSITORY}")

    def test_selector_never_targets_legacy_distributions(self) -> None:
        """No upstream owner may reappear in the selector."""
        selector = config.Infra.codegen.toolchain.beads.selector

        for legacy in ("steveyegge", "marlon-costa-dc"):
            tm.that(legacy in selector, eq=False)

    def test_version_is_the_gas_city_release_tag(self) -> None:
        """The installed version is the fork's published release tag."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.version, eq=_GOVERNED_VERSION)
        tm.that(toolchain.beads.reported_version, eq=_GOVERNED_VERSION)

    def test_reported_version_matches_the_installed_binary(self) -> None:
        """`bd version` self-reports the same version the selector installs.

        The upstream module reported 1.1.0 while installing a later commit, so
        the preflight gate compared two different identities. The fork builds
        its own tag, so both are the same string.
        """
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.reported_version, eq=toolchain.beads.version)

    def test_schema_and_linux_binary_are_canonical(self) -> None:
        beads = config.Infra.codegen.toolchain.beads

        tm.that(beads.expected_schema, eq=_GOVERNED_SCHEMA)
        tm.that(beads.checksum, eq=_LINUX_X64_SHA256)


__all__: tuple[str, ...] = ()
