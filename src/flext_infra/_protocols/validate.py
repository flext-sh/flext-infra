# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


class FlextInfraProtocolsValidate:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class NamespaceValidateCommand(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path


__all__: list[str] = [
    "FlextInfraProtocolsValidate",
]
