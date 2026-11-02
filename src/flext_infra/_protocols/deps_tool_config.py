# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsDepsToolConfig:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ToolConfigDocument(Protocol):
        """Structural data contract projected from the owning model."""

        settings: Mapping[t.NonEmptyStr, t.Infra.SettingsPairs]
        derived_tool_roots: tuple[t.NonEmptyStr, ...]
        derived_settings: Mapping[t.NonEmptyStr, tuple[t.NonEmptyStr, ...]]
        raw_check_receipt_suffix: t.NonEmptyStr
        tools: FlextInfraModelsDepsToolConfig.ToolConfigTools = ...
        lazy_init: FlextInfraModelsDepsToolConfig.LazyInitConfig = ...
        facade_members: FlextInfraModelsDepsToolConfig.FacadeMembersConfig = ...
        smells: FlextInfraModelsDepsToolConfig.SmellsConfig = ...
        accessor_policy: FlextInfraModelsDepsToolConfig.AccessorPolicyConfig = ...
        mod: FlextInfraModelsDepsToolConfig.ModConfig = ...

    @runtime_checkable
    class ToolingInputs(Protocol):
        """Structural data contract projected from the owning model."""

        document: FlextInfraModelsDepsToolConfig.ToolConfigDocument
        sources: tuple[p.Cli.AtomicFileState, ...]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfig",
]
