# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Detectors package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.refactor._detectors.class_placement_detector import (
        ClassPlacementDetector,
    )
    from flext_infra.refactor._detectors.compatibility_alias_detector import (
        CompatibilityAliasDetector,
    )
    from flext_infra.refactor._detectors.cyclic_import_detector import (
        CyclicImportDetector,
    )
    from flext_infra.refactor._detectors.dependency_analyzer_base import (
        DependencyAnalyzer,
    )
    from flext_infra.refactor._detectors.future_annotations_detector import (
        FutureAnnotationsDetector,
    )
    from flext_infra.refactor._detectors.import_alias_detector import (
        ImportAliasDetector,
    )
    from flext_infra.refactor._detectors.import_collector import ImportCollector
    from flext_infra.refactor._detectors.internal_import_detector import (
        InternalImportDetector,
    )
    from flext_infra.refactor._detectors.loose_object_detector import (
        LooseObjectDetector,
    )
    from flext_infra.refactor._detectors.manual_protocol_detector import (
        ManualProtocolDetector,
    )
    from flext_infra.refactor._detectors.manual_typing_alias_detector import (
        ManualTypingAliasDetector,
    )
    from flext_infra.refactor._detectors.module_loader import (
        DetectorScanResultBuilder,
        FlextInfraRefactorDetectorModuleLoader,
    )
    from flext_infra.refactor._detectors.mro_completeness_detector import (
        MROCompletenessDetector,
    )
    from flext_infra.refactor._detectors.namespace_facade_scanner import (
        NamespaceFacadeScanner,
    )
    from flext_infra.refactor._detectors.namespace_source_detector import (
        NamespaceSourceDetector,
    )
    from flext_infra.refactor._detectors.python_module_loader_mixin import (
        FlextInfraRefactorDetectorPythonModuleLoaderMixin,
    )
    from flext_infra.refactor._detectors.runtime_alias_detector import (
        RuntimeAliasDetector,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ClassPlacementDetector": ("flext_infra.refactor._detectors.class_placement_detector", "ClassPlacementDetector"),
    "CompatibilityAliasDetector": ("flext_infra.refactor._detectors.compatibility_alias_detector", "CompatibilityAliasDetector"),
    "CyclicImportDetector": ("flext_infra.refactor._detectors.cyclic_import_detector", "CyclicImportDetector"),
    "DependencyAnalyzer": ("flext_infra.refactor._detectors.dependency_analyzer_base", "DependencyAnalyzer"),
    "DetectorScanResultBuilder": ("flext_infra.refactor._detectors.module_loader", "DetectorScanResultBuilder"),
    "FlextInfraRefactorDetectorModuleLoader": ("flext_infra.refactor._detectors.module_loader", "FlextInfraRefactorDetectorModuleLoader"),
    "FlextInfraRefactorDetectorPythonModuleLoaderMixin": ("flext_infra.refactor._detectors.python_module_loader_mixin", "FlextInfraRefactorDetectorPythonModuleLoaderMixin"),
    "FutureAnnotationsDetector": ("flext_infra.refactor._detectors.future_annotations_detector", "FutureAnnotationsDetector"),
    "ImportAliasDetector": ("flext_infra.refactor._detectors.import_alias_detector", "ImportAliasDetector"),
    "ImportCollector": ("flext_infra.refactor._detectors.import_collector", "ImportCollector"),
    "InternalImportDetector": ("flext_infra.refactor._detectors.internal_import_detector", "InternalImportDetector"),
    "LooseObjectDetector": ("flext_infra.refactor._detectors.loose_object_detector", "LooseObjectDetector"),
    "MROCompletenessDetector": ("flext_infra.refactor._detectors.mro_completeness_detector", "MROCompletenessDetector"),
    "ManualProtocolDetector": ("flext_infra.refactor._detectors.manual_protocol_detector", "ManualProtocolDetector"),
    "ManualTypingAliasDetector": ("flext_infra.refactor._detectors.manual_typing_alias_detector", "ManualTypingAliasDetector"),
    "NamespaceFacadeScanner": ("flext_infra.refactor._detectors.namespace_facade_scanner", "NamespaceFacadeScanner"),
    "NamespaceSourceDetector": ("flext_infra.refactor._detectors.namespace_source_detector", "NamespaceSourceDetector"),
    "RuntimeAliasDetector": ("flext_infra.refactor._detectors.runtime_alias_detector", "RuntimeAliasDetector"),
}

__all__ = [
    "ClassPlacementDetector",
    "CompatibilityAliasDetector",
    "CyclicImportDetector",
    "DependencyAnalyzer",
    "DetectorScanResultBuilder",
    "FlextInfraRefactorDetectorModuleLoader",
    "FlextInfraRefactorDetectorPythonModuleLoaderMixin",
    "FutureAnnotationsDetector",
    "ImportAliasDetector",
    "ImportCollector",
    "InternalImportDetector",
    "LooseObjectDetector",
    "MROCompletenessDetector",
    "ManualProtocolDetector",
    "ManualTypingAliasDetector",
    "NamespaceFacadeScanner",
    "NamespaceSourceDetector",
    "RuntimeAliasDetector",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
