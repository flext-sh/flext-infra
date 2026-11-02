# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraProtocolsDepsToolConfigTypeCheckers:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class DiagnosticPathException(Protocol):
        """Structural data contract projected from the owning model."""

        root: t.NonEmptyStr
        rationale: t.NonEmptyStr
        authorization: p.Infra.TrackerAuthorization | p.Infra.OperatorAuthorization
        changes: tuple[p.Infra.DiagnosticRuleChange, ...]

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
