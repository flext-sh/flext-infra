"""Contract tests for the governed beads distribution pinned by the SSOT."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm

_OFFICIAL_REPOSITORY = "gastownhall/beads"


class TestsToolchainBeadsDistribution:
    """Beads installs from the official stable GitHub distribution."""

    def test_selector_targets_the_official_distribution(self) -> None:
        """The selector names the official project through the GitHub backend."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.selector, eq=f"github:{_OFFICIAL_REPOSITORY}")

    def test_selector_never_targets_a_fork(self) -> None:
        """A locally governed fork may not reappear in the selector."""
        selector = config.Infra.codegen.toolchain.beads.selector

        tm.that("marlon-costa-dc" in selector, eq=False)

    def test_release_policy_is_stable_and_content_attested(self) -> None:
        """The configured release is stable, exact, and content-attested."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.prerelease, eq=False)
        tm.that(toolchain.beads.minimum_release_age, eq=None)
        tm.that(toolchain.beads.checksum is not None, eq=True)

    def test_reported_version_matches_the_installed_binary(self) -> None:
        """The reported identity follows the exact configured release."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(toolchain.beads.reported_version, eq=toolchain.beads.version)


__all__: tuple[str, ...] = ()
