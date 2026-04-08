# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Detectors package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "DetectorContext": ("flext_infra.detectors._base_detector", "DetectorContext"),
    "FlextInfraClassPlacementDetector": (
        "flext_infra.detectors.class_placement_detector",
        "FlextInfraClassPlacementDetector",
    ),
    "FlextInfraCompatibilityAliasDetector": (
        "flext_infra.detectors.compatibility_alias_detector",
        "FlextInfraCompatibilityAliasDetector",
    ),
    "FlextInfraCyclicImportDetector": (
        "flext_infra.detectors.cyclic_import_detector",
        "FlextInfraCyclicImportDetector",
    ),
    "FlextInfraFutureAnnotationsDetector": (
        "flext_infra.detectors.future_annotations_detector",
        "FlextInfraFutureAnnotationsDetector",
    ),
    "FlextInfraImportAliasDetector": (
        "flext_infra.detectors.import_alias_detector",
        "FlextInfraImportAliasDetector",
    ),
    "FlextInfraInternalImportDetector": (
        "flext_infra.detectors.internal_import_detector",
        "FlextInfraInternalImportDetector",
    ),
    "FlextInfraLooseObjectDetector": (
        "flext_infra.detectors.loose_object_detector",
        "FlextInfraLooseObjectDetector",
    ),
    "FlextInfraMROCompletenessDetector": (
        "flext_infra.detectors.mro_completeness_detector",
        "FlextInfraMROCompletenessDetector",
    ),
    "FlextInfraManualProtocolDetector": (
        "flext_infra.detectors.manual_protocol_detector",
        "FlextInfraManualProtocolDetector",
    ),
    "FlextInfraManualTypingAliasDetector": (
        "flext_infra.detectors.manual_typing_alias_detector",
        "FlextInfraManualTypingAliasDetector",
    ),
    "FlextInfraNamespaceFacadeScanner": (
        "flext_infra.detectors.namespace_facade_scanner",
        "FlextInfraNamespaceFacadeScanner",
    ),
    "FlextInfraNamespaceSourceDetector": (
        "flext_infra.detectors.namespace_source_detector",
        "FlextInfraNamespaceSourceDetector",
    ),
    "FlextInfraRuntimeAliasDetector": (
        "flext_infra.detectors.runtime_alias_detector",
        "FlextInfraRuntimeAliasDetector",
    ),
    "FlextInfraScanFileMixin": (
        "flext_infra.detectors._base_detector",
        "FlextInfraScanFileMixin",
    ),
    "class_placement_detector": "flext_infra.detectors.class_placement_detector",
    "compatibility_alias_detector": "flext_infra.detectors.compatibility_alias_detector",
    "cyclic_import_detector": "flext_infra.detectors.cyclic_import_detector",
    "future_annotations_detector": "flext_infra.detectors.future_annotations_detector",
    "import_alias_detector": "flext_infra.detectors.import_alias_detector",
    "internal_import_detector": "flext_infra.detectors.internal_import_detector",
    "loose_object_detector": "flext_infra.detectors.loose_object_detector",
    "manual_protocol_detector": "flext_infra.detectors.manual_protocol_detector",
    "manual_typing_alias_detector": "flext_infra.detectors.manual_typing_alias_detector",
    "mro_completeness_detector": "flext_infra.detectors.mro_completeness_detector",
    "namespace_facade_scanner": "flext_infra.detectors.namespace_facade_scanner",
    "namespace_source_detector": "flext_infra.detectors.namespace_source_detector",
    "runtime_alias_detector": "flext_infra.detectors.runtime_alias_detector",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
