"""Contract tests for generated toolchain requirement expressions."""

from __future__ import annotations

from flext_infra import config
from flext_tests import tm


class TestsToolchainRequirement:
    """The generated surface uses the caller-managed uv executable."""

    def test_uv_has_no_project_owned_version_pin(self) -> None:
        """Keep uv version selection outside the project configuration."""
        toolchain = config.Infra.codegen.toolchain
        payload = toolchain.model_dump()

        tm.that(payload, lacks="uv_version")
        tm.that(payload, lacks="uv_required_version")
