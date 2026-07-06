# AUTO-GENERATED FILE — Regenerate with: make gen
"""Enforcement package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._enforcement.collection_base import (
        FlextInfraEnforcementCollectionBase as FlextInfraEnforcementCollectionBase,
        FlextInfraEnforcementEvaluation as FlextInfraEnforcementEvaluation,
    )
    from flext_infra._enforcement.collection_sources import (
        FlextInfraEnforcementSourceCollectors as FlextInfraEnforcementSourceCollectors,
    )
    from flext_infra._enforcement.collection_tests import (
        FlextInfraEnforcementTestsCollector as FlextInfraEnforcementTestsCollector,
    )
    from flext_infra._enforcement.engine import (
        FlextInfraEnforcementEngine as FlextInfraEnforcementEngine,
    )
    from flext_infra._enforcement.metadata import (
        FlextInfraEnforcementMetadata as FlextInfraEnforcementMetadata,
    )
    from flext_infra._enforcement.selection import (
        FlextInfraEnforcementSelection as FlextInfraEnforcementSelection,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".collection_base": (
            "FlextInfraEnforcementCollectionBase",
            "FlextInfraEnforcementEvaluation",
        ),
        ".collection_sources": ("FlextInfraEnforcementSourceCollectors",),
        ".collection_tests": ("FlextInfraEnforcementTestsCollector",),
        ".engine": ("FlextInfraEnforcementEngine",),
        ".metadata": ("FlextInfraEnforcementMetadata",),
        ".selection": ("FlextInfraEnforcementSelection",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
