# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsCodegenFix:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ConsolidatorFileResult(Protocol):
        """Structural data contract projected from the owning model."""

        file: t.NonEmptyStr
        status: Literal["applied", "reverted"]
        changes: Sequence[str] = ...

    @runtime_checkable
    class ConsolidatorReport(Protocol):
        """Structural data contract projected from the owning model."""

        total_found: t.NonNegativeInt = ...
        total_applied: t.NonNegativeInt = ...
        total_failed: t.NonNegativeInt = ...
        files: Sequence[FlextInfraModelsCodegenFix.ConsolidatorFileResult] = ...

    @runtime_checkable
    class FacadeFamily(Protocol):
        """Structural data contract projected from the owning model."""

        letter: t.NonEmptyStr
        module: t.NonEmptyStr
        suffix: t.NonEmptyStr

    @runtime_checkable
    class ViolationKey(Protocol):
        """Structural data contract projected from the owning model."""

        module: str
        rule: str
        content_hash: str


__all__: list[str] = [
    "FlextInfraProtocolsCodegenFix",
]
