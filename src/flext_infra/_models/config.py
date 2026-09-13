"""Pure Pydantic config and codegen contracts for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u

from .. import t
from .mise_toolchain import FlextInfraModelsMiseToolchain


def _tool_version_field(description: str) -> object:
    """Shared ``Annotated[t.NonEmptyStr, ...]`` metadata for one tool version.

    Every native-toolchain version field in ``ToolchainSpec`` and its
    ``ProjectRenderContext`` render mirror previously repeated an identical
    ``m.Field(description=...)`` shape, differing only in the description
    text -- a structural clone SonarCloud's duplication detector flags as one
    family regardless of the literal string. One owned factory collapses
    every call site to this single declaration (SSOT, DRY).
    """
    return m.Field(description=description)


class FlextInfraConfigModels:
    """Field-only models for config loading and codegen plans."""

    # These models replace the former model-less workspace/make dictionaries.
    # YAML is accepted only at the flext-cli loading boundary and is immediately
    # model-validated here.

    class _ConfigContract(m.ContractModel):
        """Private declarative base for schema-loaded codegen records."""

        # Rendered file payloads are
        # byte contracts; Pydantic must never trim their final newline.
        model_config = m.ConfigDict(
            strict=False, frozen=True, extra="forbid", str_strip_whitespace=False
        )

    # Re-export mise toolchain models from single source of truth
    MiseToolSpec = FlextInfraModelsMiseToolchain.MiseToolSpec
    ProtectedMiseToolSpec = FlextInfraModelsMiseToolchain.ProtectedMiseToolSpec
    BeadsEndpointSpec = FlextInfraModelsMiseToolchain.BeadsEndpointSpec
    BeadsToolSpec = FlextInfraModelsMiseToolchain.BeadsToolSpec
    MiseBootstrapEnvironmentSpec = FlextInfraModelsMiseToolchain.MiseBootstrapEnvironmentSpec
    ToolchainSpec = FlextInfraModelsMiseToolchain.ToolchainSpec

    class BeadsProjectSpec(_ConfigContract):
        """Beads projection contract for one subproject's generated surface."""

        project_name: Annotated[
            t.NonEmptyStr, m.Field(description="Target subproject package name")
        ]
        rig_id: Annotated[
            t.NonEmptyStr, m.Field(description="Gas City rig identifier for this project")
        ]
        dolt_mode: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Rendered as dolt.mode in .beads/config.yaml"
            ),
        ]
        export_auto: Annotated[
            bool,
            m.Field(description="Rendered as export.auto in .beads/config.yaml"),
        ]
        backup_enabled: Annotated[
            bool,
            m.Field(description="Rendered as backup.enabled in .beads/config.yaml"),
        ]
        dolt_disable_event_flush: Annotated[
            bool,
            m.Field(
                description="Rendered as dolt.disable-event-flush in .beads/config.yaml"
            ),
        ]
        required_custom_types: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Immutable custom bead types required by this project",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_project_spec(self) -> Self:
            """Require unambiguous rig and type declarations."""
            if len(set(self.required_custom_types)) != len(self.required_custom_types):
                msg = "beads required_custom_types must be unique per project"
                raise ValueError(msg)
            return self

    class BeadsConfigRenderSpec(_ConfigContract):
        """Rendered ``.beads/config.yaml`` contract for one project."""

        project: Annotated[t.NonEmptyStr, m.Field(description="Project package name")]
        rig: Annotated[t.NonEmptyStr, m.Field(description="Gas City rig identifier")]
        dolt: Annotated[t.MappingKV[t.NonEmptyStr, t.JsonValue], m.Field(description="Dolt configuration")]
        export: Annotated[t.MappingKV[t.NonEmptyStr, t.JsonValue], m.Field(description="Export configuration")]
        backup: Annotated[t.MappingKV[t.NonEmptyStr, t.JsonValue], m.Field(description="Backup configuration")]
        custom_types: Annotated[t.SequenceOf[t.NonEmptyStr], m.Field(description="Required custom bead types")]

    class MiseTomlRenderSpec(ToolchainSpec):
        """Rendered ``.mise.toml`` contract mirroring the declarative toolchain."""

    class BeadsMetadataRenderSpec(_ConfigContract):
        """Rendered ``.beads/metadata.yaml`` contract for one project."""

        project: Annotated[t.NonEmptyStr, m.Field(description="Project package name")]
        rig: Annotated[t.NonEmptyStr, m.Field(description="Gas City rig identifier")]
        generated_at: Annotated[t.NonEmptyStr, m.Field(description="ISO-8601 generation timestamp")]
        toolchain_hash: Annotated[t.NonEmptyStr, m.Field(description="SHA256 of the generating toolchain config")]

    class WorkspaceBeadsServerSpec(_ConfigContract):
        """Workspace-level Beads server configuration contract."""

        host: Annotated[t.NonEmptyStr, m.Field(description="Beads server host")]
        port: Annotated[int, m.Field(ge=1, le=65535, description="Beads server TCP port")]
        dolt_mode: Annotated[t.NonEmptyStr, m.Field(description="Dolt mode for workspace")]
        export_auto: Annotated[bool, m.Field(description="Export auto flag for workspace")]
        backup_enabled: Annotated[bool, m.Field(description="Backup enabled flag for workspace")]
        dolt_disable_event_flush: Annotated[bool, m.Field(description="Dolt disable event flush flag")]
        required_custom_types: Annotated[t.SequenceOf[t.NonEmptyStr], m.Field(description="Required custom bead types")]

    class BeadsWorkspaceEnvironmentSpec(_ConfigContract):
        """Workspace-level Beads environment contract for generation."""

        beads_server: Annotated[
            FlextInfraConfigModels.WorkspaceBeadsServerSpec,
            m.Field(description="Beads server configuration"),
        ]
        project_overrides: Annotated[
            t.MappingKV[t.NonEmptyStr, FlextInfraConfigModels.BeadsProjectSpec],
            m.Field(description="Per-project Beads overrides"),
        ]

    class CodegenProjectSpec(_ConfigContract):
        """Codegen project declaration from ``codegen.yaml``."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Subproject package name")]
        role: Annotated[Literal["internal_flext", "external"], m.Field(description="Project role")]
        kind: Annotated[Literal["library", "service", "cli"], m.Field(description="Project kind")]
        dependencies: Annotated[t.SequenceOf[t.NonEmptyStr], m.Field(description="Internal dependencies")]
        config: Annotated[t.MappingKV[t.NonEmptyStr, t.JsonValue], m.Field(description="Project config")]

    class MakeSpec(_ConfigContract):
        """Make verb contract for generated ``Makefile``."""

        verb: Annotated[t.NonEmptyStr, m.Field(description="Make verb name")]
        deps: Annotated[t.SequenceOf[t.NonEmptyStr], m.Field(description="Make dependencies")]
        recipe: Annotated[t.NonEmptyStr, m.Field(description="Make recipe body")]
        phony: Annotated[bool, m.Field(default=False, description="Phony target")]

    class ReleaseSpec(_ConfigContract):
        """Release contract for generated release automation."""

        version: Annotated[t.NonEmptyStr, m.Field(description="Release version")]
        changelog: Annotated[t.NonEmptyStr, m.Field(description="Changelog content")]
        artifacts: Annotated[t.SequenceOf[t.NonEmptyStr], m.Field(description="Release artifacts")]

    class SharedInfraSpec(_ConfigContract):
        """Shared infrastructure contract for generated surfaces."""

        shared: Annotated[t.MappingKV[t.NonEmptyStr, t.JsonValue], m.Field(description="Shared infra config")]

    class ProjectRenderContext(m.BaseModel):
        """Complete render context for one project's generated files."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid")

        project: Annotated[t.NonEmptyStr, m.Field(description="Project package name")]
        role: Annotated[Literal["internal_flext", "external"], m.Field(description="Project role")]
        kind: Annotated[Literal["library", "service", "cli"], m.Field(description="Project kind")]
        toolchain: ToolchainSpec  # ruff: ignore[undefined-name]
        beads_project: BeadsProjectSpec  # ruff: ignore[undefined-name]
        make_verbs: Annotated[t.SequenceOf[FlextInfraConfigModels.MakeSpec], m.Field(description="Make verbs")]
        release: FlextInfraConfigModels.ReleaseSpec
        shared_infra: FlextInfraConfigModels.SharedInfraSpec

    class WorkspaceRenderContext(m.BaseModel):
        """Complete render context for workspace-level generated files."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid")

        workspace_name: Annotated[t.NonEmptyStr, m.Field(description="Workspace package name")]
        toolchain: ToolchainSpec  # ruff: ignore[undefined-name]
        beads_server: FlextInfraConfigModels.WorkspaceBeadsServerSpec
        beads_environment: FlextInfraConfigModels.BeadsWorkspaceEnvironmentSpec
        projects: Annotated[
            t.SequenceOf[FlextInfraConfigModels.ProjectRenderContext],
            m.Field(description="All project render contexts"),
        ]


__all__: list[str] = ["FlextInfraConfigModels", "_tool_version_field"]

# Re-export mise toolchain models from single source of truth (module level)
MiseToolSpec = FlextInfraModelsMiseToolchain.MiseToolSpec
ProtectedMiseToolSpec = FlextInfraModelsMiseToolchain.ProtectedMiseToolSpec
BeadsEndpointSpec = FlextInfraModelsMiseToolchain.BeadsEndpointSpec
BeadsToolSpec = FlextInfraModelsMiseToolchain.BeadsToolSpec
MiseBootstrapEnvironmentSpec = FlextInfraModelsMiseToolchain.MiseBootstrapEnvironmentSpec
ToolchainSpec = FlextInfraModelsMiseToolchain.ToolchainSpec
