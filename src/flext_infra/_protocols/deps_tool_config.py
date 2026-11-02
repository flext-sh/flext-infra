# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from flext_infra import p, t


class FlextInfraProtocolsDepsToolConfig:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ToolConfigDocument(Protocol):
        """Structural data contract projected from the owning model."""

        settings: Mapping[t.NonEmptyStr, t.Infra.SettingsPairs]
        derived_tool_roots: tuple[t.NonEmptyStr, ...]
        derived_settings: Mapping[t.NonEmptyStr, tuple[t.NonEmptyStr, ...]]
        raw_check_receipt_suffix: t.NonEmptyStr
        tools: FlextInfraProtocolsDepsToolConfig.ToolConfigTools = ...
        lazy_init: FlextInfraProtocolsDepsToolConfig.LazyInitConfig = ...
        facade_members: FlextInfraProtocolsDepsToolConfig.FacadeMembersConfig = ...
        smells: FlextInfraProtocolsDepsToolConfig.SmellsConfig = ...
        accessor_policy: FlextInfraProtocolsDepsToolConfig.AccessorPolicyConfig = ...
        mod: FlextInfraProtocolsDepsToolConfig.ModConfig = ...

    @runtime_checkable
    class ToolingInputs(Protocol):
        """Structural data contract projected from the owning model."""

        document: FlextInfraProtocolsDepsToolConfig.ToolConfigDocument
        sources: tuple[p.Cli.AtomicFileState, ...]


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfig",
]
