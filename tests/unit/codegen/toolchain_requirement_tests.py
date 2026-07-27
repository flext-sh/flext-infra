"""Contract tests for the generated toolchain requirement expressions.

Both requirement expressions are derived from a single declared version, so a
bump touches exactly one value. The expressions must also survive the window in
which projects are still propagating a new SSOT: a consumer that is one patch
ahead or behind must keep working, otherwise every `make` command in that
project aborts before it can even sync itself back into conformance.
"""

from __future__ import annotations

from flext_infra import config


class TestsToolchainRequirement:
    """Requirement expressions tolerate patch drift and pin the minor."""

    def test_python_requirement_pins_floor_and_next_minor_ceiling(self) -> None:
        """The Python expression is the reference shape for every toolchain pin."""
        toolchain = config.Infra.codegen.toolchain
        assert toolchain.python_required_version.startswith(
            f">={toolchain.python_version},<"
        )

    def test_uv_requirement_admits_a_newer_patch(self) -> None:
        """A consumer one patch ahead must not be locked out.

        Projects adopt a new toolchain at different times. While a bump is
        propagating, an exact `==` pin turns every uv invocation into a hard
        failure, which blocks the very `make` run that would bring the project
        back into conformance. The floor still forbids anything older than the
        declared version.
        """
        toolchain = config.Infra.codegen.toolchain
        assert toolchain.uv_required_version.startswith(f">={toolchain.uv_version},<")

    def test_uv_requirement_forbids_the_next_minor(self) -> None:
        """Tolerance stops at the minor boundary.

        Patch releases are compatible; a minor bump is a coordinated migration
        and must still be refused until the SSOT declares it.
        """
        toolchain = config.Infra.codegen.toolchain
        major, _, rest = toolchain.uv_version.partition(".")
        minor, _, _patch = rest.partition(".")
        assert toolchain.uv_required_version.endswith(f",<{major}.{int(minor) + 1}")
