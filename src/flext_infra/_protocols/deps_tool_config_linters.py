# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsDepsToolConfigLinters:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class TrackerAuthorization(Protocol):
        """Structural data contract projected from the owning model."""

        tracker_key: t.NonEmptyStr

    @runtime_checkable
    class OperatorAuthorization(Protocol):
        """Structural data contract projected from the owning model."""

        operator_words: t.NonEmptyStr
        authorized_on: date
        channel: t.NonEmptyStr

    @runtime_checkable
    class DiagnosticRuleChange(Protocol):
        """Structural data contract projected from the owning model."""

        checker: t.NonEmptyStr
        rule: t.NonEmptyStr
        old: t.NonEmptyStr
        new: t.NonEmptyStr


__all__: list[str] = [
    "FlextInfraProtocolsDepsToolConfigLinters",
]
