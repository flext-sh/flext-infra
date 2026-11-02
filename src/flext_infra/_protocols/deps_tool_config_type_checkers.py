# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from flext_infra import t
from flext_infra._models import FlextInfraModelsDepsToolConfigLinters


class FlextInfraProtocolsDepsToolConfigTypeCheckers:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class DiagnosticPathException(Protocol):
        """Structural data contract projected from the owning model."""

        root: t.NonEmptyStr
        rationale: t.NonEmptyStr
        authorization: (
            FlextInfraModelsDepsToolConfigLinters.TrackerAuthorization
            | FlextInfraModelsDepsToolConfigLinters.OperatorAuthorization
        )
        changes: tuple[FlextInfraModelsDepsToolConfigLinters.DiagnosticRuleChange, ...]

    @runtime_checkable
    class ExecutionEnvironment(Protocol):
        """Structural data contract projected from the owning model."""

        root: str
        report_private_usage: str
        extra_paths: Sequence[str]
        diagnostic_levels: Mapping[str, str] = ...


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigTypeCheckers",
]
