"""FLEXT infrastructure check service namespace."""

from __future__ import annotations

from flext_infra import FlextInfraConfigFixer, FlextInfraWorkspaceChecker


class FlextInfraCheckServices:
    """Canonical check service namespace for public check package exports."""

    FlextInfraWorkspaceChecker = FlextInfraWorkspaceChecker
    FlextInfraConfigFixer = FlextInfraConfigFixer


__all__ = ["FlextInfraCheckServices"]
