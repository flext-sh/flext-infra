"""Contract tests for generated toolchain requirement expressions."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsToolchainRequirement:
    """Toolchain requirements tolerate compatible Python patch drift."""

    def test_python_requirement_uses_declared_minor_as_floor(self) -> None:
        """The declared Python minor remains the lower compatibility bound."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(
            toolchain.python_required_version, has=f">={toolchain.python_version},<"
        )

    def test_python_requirement_rejects_the_next_minor(self) -> None:
        """Python minor upgrades remain an explicit SSOT migration."""
        toolchain = config.Infra.codegen.toolchain
        major, _, minor = toolchain.python_version.partition(".")

        tm.that(toolchain.python_required_version, has=f",<{major}.{int(minor) + 1}")

    def test_uv_cooldown_is_derived_from_shared_days(self) -> None:
        """Uv and dependency-update automation share one cooldown value."""
        toolchain = config.Infra.codegen.toolchain

        tm.that(
            toolchain.uv_exclude_newer, eq=f"{toolchain.dependency_cooldown_days} days"
        )
        tm.that(toolchain.dependency_cooldown_exclusions, has="cryptography")


__all__: tuple[str, ...] = ()
