# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Detectors package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "DetectorContext": "._base_detector",
    "FlextInfraClassPlacementDetector": ".class_placement_detector",
    "FlextInfraCompatibilityAliasDetector": ".compatibility_alias_detector",
    "FlextInfraCyclicImportDetector": ".cyclic_import_detector",
    "FlextInfraFutureAnnotationsDetector": ".future_annotations_detector",
    "FlextInfraImportAliasDetector": ".import_alias_detector",
    "FlextInfraInternalImportDetector": ".internal_import_detector",
    "FlextInfraLooseObjectDetector": ".loose_object_detector",
    "FlextInfraMROCompletenessDetector": ".mro_completeness_detector",
    "FlextInfraManualProtocolDetector": ".manual_protocol_detector",
    "FlextInfraManualTypingAliasDetector": ".manual_typing_alias_detector",
    "FlextInfraNamespaceFacadeScanner": ".namespace_facade_scanner",
    "FlextInfraNamespaceSourceDetector": ".namespace_source_detector",
    "FlextInfraRuntimeAliasDetector": ".runtime_alias_detector",
    "FlextInfraScanFileMixin": "._base_detector",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
