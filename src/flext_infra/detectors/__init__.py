# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.detectors package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .class_placement_detector import FlextInfraClassPlacementDetector
    from .compatibility_alias_detector import FlextInfraCompatibilityAliasDetector
    from .cyclic_import_detector import FlextInfraCyclicImportDetector
    from .deferred_self_reference_detector import (
        FlextInfraDeferredSelfReferenceDetector,
    )
    from .facade_scanner import FlextInfraScanner
    from .future_annotations_detector import FlextInfraFutureAnnotationsDetector
    from .import_alias_detector import FlextInfraImportAliasDetector
    from .inline_import_detector import FlextInfraInlineImportDetector
    from .internal_import_detector import FlextInfraInternalImportDetector
    from .loose_object_detector import FlextInfraLooseObjectDetector
    from .loose_test_function_detector import FlextInfraLooseTestFunctionDetector
    from .manual_protocol_detector import FlextInfraManualProtocolDetector
    from .manual_typing_alias_detector import FlextInfraManualTypingAliasDetector
    from .mro_completeness_detector import FlextInfraMROCompletenessDetector
    from .mro_shape_detector import FlextInfraMROShapeDetector
    from .namespace_source_detector import FlextInfraNamespaceSourceDetector
    from .private_import_bypass_detector import FlextInfraPrivateImportBypassDetector
    from .runtime_alias_detector import FlextInfraRuntimeAliasDetector
    from .silent_failure_detector import FlextInfraSilentFailureDetector

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".class_placement_detector": ("FlextInfraClassPlacementDetector",),
    ".compatibility_alias_detector": ("FlextInfraCompatibilityAliasDetector",),
    ".cyclic_import_detector": ("FlextInfraCyclicImportDetector",),
    ".deferred_self_reference_detector": ("FlextInfraDeferredSelfReferenceDetector",),
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

__all__: tuple[str, ...] = (
    "FlextInfraClassPlacementDetector",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDeferredSelfReferenceDetector",
    "FlextInfraFutureAnnotationsDetector",
    "FlextInfraImportAliasDetector",
    "FlextInfraInlineImportDetector",
    "FlextInfraInternalImportDetector",
    "FlextInfraLooseObjectDetector",
    "FlextInfraLooseTestFunctionDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraMROShapeDetector",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraPrivateImportBypassDetector",
    "FlextInfraRuntimeAliasDetector",
    "FlextInfraScanner",
    "FlextInfraSilentFailureDetector",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
