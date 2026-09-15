"""Shared contract base and root aliases for config models."""

from __future__ import annotations

from typing import Annotated

from flext_cli import m

from .. import immutable_empty_mapping
from ..mise_toolchain import FlextInfraModelsMiseToolchain


class FlextInfraConfigModelsContract:
    """Shared contract base and root aliases for config models."""

    class ConfigContract(m.ContractModel):
        """Public declarative base for schema-loaded codegen records."""

        # Rendered file payloads are
        # byte contracts; Pydantic must never trim their final newline.
        model_config = m.ConfigDict(
            strict=False, frozen=True, extra="forbid", str_strip_whitespace=False
        )

    immutable_empty_mapping = immutable_empty_mapping
    MiseToolSpec = FlextInfraModelsMiseToolchain.MiseToolSpec
    ProtectedMiseToolSpec = FlextInfraModelsMiseToolchain.ProtectedMiseToolSpec
    BeadsEndpointSpec = FlextInfraModelsMiseToolchain.BeadsEndpointSpec
    BeadsToolSpec = FlextInfraModelsMiseToolchain.BeadsToolSpec
    MiseBootstrapEnvironmentSpec = (
        FlextInfraModelsMiseToolchain.MiseBootstrapEnvironmentSpec
    )
    ToolchainSpec = FlextInfraModelsMiseToolchain.ToolchainSpec

    class MiseTomlRenderSpec(ToolchainSpec):
        """Toolchain render context for ``.mise.toml`` plus per-project gates.

        The template consumes flat toolchain field names, so the context is the
        fleet ToolchainSpec narrowed by the per-project Gas City participation
        resolved from the workspace manifest overlay.
        """

        gascity_enabled: Annotated[
            bool,
            m.Field(
                description=("Whether the gc tool block is projected into .mise.toml.")
            ),
        ] = True


# Rebuild MiseTomlRenderSpec after all imports are resolved.
# This must happen at module level after FlextInfraModelsMiseToolchain
# and its nested classes are fully loaded by the lazy import mechanism.
# Per FLEXT strict rules, model_rebuild is normally avoided, but this is
# a documented Pydantic limitation with cross-module nested class inheritance
# under lazy loading. The rebuild happens at module import time, before any
# runtime use, so it does not affect correctness or introduce shims.
FlextInfraConfigModelsContract.MiseTomlRenderSpec.model_rebuild()

