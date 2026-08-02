# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.detectors package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".class_placement_detector": ("FlextInfraClassPlacementDetector",),
    ".compatibility_alias_detector": ("FlextInfraCompatibilityAliasDetector",),
    ".cyclic_import_detector": ("FlextInfraCyclicImportDetector",),
    ".facade_scanner": ("FlextInfraScanner",),
    ".future_annotations_detector": ("FlextInfraFutureAnnotationsDetector",),
    ".import_alias_detector": ("FlextInfraImportAliasDetector",),
    ".inline_import_detector": ("FlextInfraInlineImportDetector",),
    ".internal_import_detector": ("FlextInfraInternalImportDetector",),
    ".loose_object_detector": ("FlextInfraLooseObjectDetector",),
    ".loose_test_function_detector": ("FlextInfraLooseTestFunctionDetector",),
    ".manual_protocol_detector": ("FlextInfraManualProtocolDetector",),
    ".manual_typing_alias_detector": ("FlextInfraManualTypingAliasDetector",),
    ".mro_completeness_detector": ("FlextInfraMROCompletenessDetector",),
    ".mro_shape_detector": ("FlextInfraMROShapeDetector",),
    ".namespace_source_detector": ("FlextInfraNamespaceSourceDetector",),
    ".private_import_bypass_detector": ("FlextInfraPrivateImportBypassDetector",),
    ".runtime_alias_detector": ("FlextInfraRuntimeAliasDetector",),
    ".silent_failure_detector": ("FlextInfraSilentFailureDetector",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
