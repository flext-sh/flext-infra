# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsRefactorNamespaceEnforcer:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ParseFailureViolation(Protocol):
        """Structural data contract projected from the owning model."""

        stage: t.NonEmptyStr
        error_type: t.NonEmptyStr


__all__: list[str] = [
    "FlextInfraProtocolsRefactorNamespaceEnforcer",
]
