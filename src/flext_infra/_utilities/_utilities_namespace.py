"""Namespace enforcement rewriting utilities composed from focused helpers."""

from __future__ import annotations

from flext_infra import (
    FlextInfraUtilitiesRefactorNamespaceFacades,
    FlextInfraUtilitiesRefactorNamespaceMoves,
    FlextInfraUtilitiesRefactorNamespaceMro,
    FlextInfraUtilitiesRefactorNamespaceRuntime,
)


class FlextInfraUtilitiesRefactorNamespace(
    FlextInfraUtilitiesRefactorNamespaceFacades,
    FlextInfraUtilitiesRefactorNamespaceRuntime,
    FlextInfraUtilitiesRefactorNamespaceMro,
    FlextInfraUtilitiesRefactorNamespaceMoves,
):
    """Namespace enforcement rewriting utilities composed via focused helpers."""
