# AUTO-GENERATED FILE — Regenerate with: make gen
"""Detectors package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._base_detector": (
            "DetectorContext",
            "FlextInfraScanFileMixin",
        ),
        ".class_placement_detector": ("FlextInfraClassPlacementDetector",),
        ".compatibility_alias_detector": ("FlextInfraCompatibilityAliasDetector",),
        ".cyclic_import_detector": ("FlextInfraCyclicImportDetector",),
        ".facade_scanner": ("FlextInfraUtilitiesFacadeScanner",),
        ".future_annotations_detector": ("FlextInfraFutureAnnotationsDetector",),
        ".import_alias_detector": ("FlextInfraImportAliasDetector",),
        ".internal_import_detector": ("FlextInfraInternalImportDetector",),
        ".loose_object_detector": ("FlextInfraLooseObjectDetector",),
        ".manual_protocol_detector": ("FlextInfraManualProtocolDetector",),
        ".manual_typing_alias_detector": ("FlextInfraManualTypingAliasDetector",),
        ".mro_completeness_detector": ("FlextInfraMROCompletenessDetector",),
        ".namespace_source_detector": ("FlextInfraNamespaceSourceDetector",),
        ".runtime_alias_detector": ("FlextInfraRuntimeAliasDetector",),
        ".silent_failure_detector": ("FlextInfraSilentFailureDetector",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
