"""Contract tests for generated toolchain requirement expressions."""

from __future__ import annotations

from flext_infra import config


class TestsToolchainRequirement:
    """Toolchain requirements tolerate compatible patch drift."""

    def test_uv_requirement_uses_declared_patch_as_floor(self) -> None:
        """The declared baseline remains the lower compatibility bound."""
        toolchain = config.Infra.codegen.toolchain

        assert toolchain.uv_required_version.startswith(
            f">={toolchain.uv_version},<"
        )

    def test_uv_requirement_rejects_the_next_minor(self) -> None:
        """Minor upgrades remain an explicit SSOT migration."""
        toolchain = config.Infra.codegen.toolchain
        major, _, rest = toolchain.uv_version.partition(".")
        minor, _, _patch = rest.partition(".")

        assert toolchain.uv_required_version.endswith(f",<{major}.{int(minor) + 1}")
