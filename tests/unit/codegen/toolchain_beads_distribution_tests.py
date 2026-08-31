"""Contracts for fleet-owned mise identities and the Beads distribution."""

from __future__ import annotations

from fnmatch import fnmatchcase

import pytest

from flext_infra import c, config, m
from flext_tests import tm

_CANONICAL_SELECTOR = "github:marlon-costa-dc/beads"
_CANONICAL_VERSION = "1.2.2-fd1"


class TestsToolchainBeadsDistribution:
    """Beads installs from the fleet's declared GitHub distribution.

    The fleet pins the operator's fork because it carries 4c1c40337
    ``fix(list): stop bd list from looping forever on hierarchy cycles``,
    absent from upstream v1.2.2.
    """

    def test_beads_selector_is_protected_by_declared_patterns(self) -> None:
        """Resolve protected owners from data and cover their canonical selector."""
        toolchain = config.Infra.codegen.toolchain
        protected = tuple(
            getattr(toolchain, owner) for owner in toolchain.protected_mise_tools
        )

        tm.that(toolchain.beads in protected, eq=True)
        tm.that(
            any(
                fnmatchcase(toolchain.beads.selector, pattern)
                for pattern in toolchain.beads.selector_patterns
            ),
            eq=True,
        )

    def test_release_policy_is_stable_and_exact(self) -> None:
        """Keep resolution stable; content attestation belongs to mise.lock."""
        toolchain = config.Infra.codegen.toolchain
        version = toolchain.beads.version
        core, _, suffix = version.partition("-")

        tm.that(toolchain.beads.minimum_release_age, eq=None)
        tm.that(toolchain.beads.selector, eq=_CANONICAL_SELECTOR)
        tm.that(version, eq=_CANONICAL_VERSION)
        tm.that(core.count("."), eq=2)
        tm.that(all(part.isdecimal() for part in core.split(".")), eq=True)
        # A suffixed tag is still one exact artifact, but mise only resolves it
        # when prerelease is declared: the two must agree or resolution breaks.
        tm.that(toolchain.beads.prerelease, eq=bool(suffix))

    def test_protected_selector_rejects_uncovered_pattern_set(self) -> None:
        """Fail config loading when canonical and protected selector families diverge."""
        beads = config.Infra.codegen.toolchain.beads

        with pytest.raises(c.ValidationError, match="not covered"):
            m.Infra.ProtectedMiseToolSpec(
                selector_patterns=("registry:unrelated",),
                selector=beads.selector,
                version=beads.version,
            )


__all__: tuple[str, ...] = ()
