"""Contract tests for generated toolchain requirement expressions."""

from __future__ import annotations

from flext_infra import config, m


class TestsToolchainRequirement:
    """Toolchain requirements tolerate compatible patch drift."""

    def test_uv_requirement_uses_configured_baseline_as_floor(self) -> None:
        toolchain = config.Infra.codegen.toolchain

        assert toolchain.uv_required_version.startswith(
            f">={toolchain.uv_version},<"
        )

    def test_uv_requirement_caps_the_configured_minor_line(self) -> None:
        toolchain = config.Infra.codegen.toolchain
        major, _, rest = toolchain.uv_version.partition(".")
        minor, _, _patch = rest.partition(".")

        assert toolchain.uv_required_version.endswith(f",<{major}.{int(minor) + 1}")

    def test_uv_requirement_derives_from_arbitrary_fixture_input(self) -> None:
        toolchain = m.Infra.ToolchainSpec(
            python_version="3.13.11",
            uv_version="7.23.41",
            uv_link_mode="copy",
            kubectl_version="1.32.0",
            helm_version="3.19.4",
            kind_version="0.31.0",
        )

        assert toolchain.uv_required_version == ">=7.23.41,<7.24"
