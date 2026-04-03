"""Namespace enforcement rewriting utilities composed from focused helpers."""

from __future__ import annotations

from flext_infra.refactor._utilities_namespace_facades import (
    FlextInfraUtilitiesRefactorNamespaceFacades,
)
from flext_infra.refactor._utilities_namespace_moves import (
    FlextInfraUtilitiesRefactorNamespaceMoves,
)
from flext_infra.refactor._utilities_namespace_mro import (
    FlextInfraUtilitiesRefactorNamespaceMro,
)
from flext_infra.refactor._utilities_namespace_runtime import (
    FlextInfraUtilitiesRefactorNamespaceRuntime,
)


class FlextInfraUtilitiesRefactorNamespace(
    FlextInfraUtilitiesRefactorNamespaceFacades,
    FlextInfraUtilitiesRefactorNamespaceRuntime,
    FlextInfraUtilitiesRefactorNamespaceMro,
    FlextInfraUtilitiesRefactorNamespaceMoves,
):
    """Namespace enforcement rewriting utilities composed via focused helpers."""


__all__ = ["FlextInfraUtilitiesRefactorNamespace"]
