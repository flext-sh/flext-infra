# AUTO-GENERATED FILE — Regenerate with: make gen
"""Detectors package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector,
    )
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector,
    )
    from flext_infra.detectors.facade_scanner import FlextInfraScanner
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector,
    )
    from flext_infra.detectors.inline_import_detector import (
        FlextInfraInlineImportDetector,
    )
    from flext_infra.detectors.internal_import_detector import (
        FlextInfraInternalImportDetector,
    )
    from flext_infra.detectors.loose_object_detector import (
        FlextInfraLooseObjectDetector,
    )
    from flext_infra.detectors.manual_protocol_detector import (
        FlextInfraManualProtocolDetector,
    )
    from flext_infra.detectors.manual_typing_alias_detector import (
        FlextInfraManualTypingAliasDetector,
    )
    from flext_infra.detectors.mro_completeness_detector import (
        FlextInfraMROCompletenessDetector,
    )
    from flext_infra.detectors.mro_shape_detector import FlextInfraMROShapeDetector
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.pattern_smell_detector import (
        FlextInfraPatternSmellDetector,
    )
    from flext_infra.detectors.private_import_bypass_detector import (
        FlextInfraPrivateImportBypassDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector,
    )
    from flext_infra.detectors.silent_failure_detector import (
        FlextInfraSilentFailureDetector,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".class_placement_detector": ("FlextInfraClassPlacementDetector",),
        ".compatibility_alias_detector": ("FlextInfraCompatibilityAliasDetector",),
        ".cyclic_import_detector": ("FlextInfraCyclicImportDetector",),
        ".facade_scanner": ("FlextInfraScanner",),
        ".future_annotations_detector": ("FlextInfraFutureAnnotationsDetector",),
        ".import_alias_detector": ("FlextInfraImportAliasDetector",),
        ".inline_import_detector": ("FlextInfraInlineImportDetector",),
        ".internal_import_detector": ("FlextInfraInternalImportDetector",),
        ".loose_object_detector": ("FlextInfraLooseObjectDetector",),
        ".manual_protocol_detector": ("FlextInfraManualProtocolDetector",),
        ".manual_typing_alias_detector": ("FlextInfraManualTypingAliasDetector",),
        ".mro_completeness_detector": ("FlextInfraMROCompletenessDetector",),
        ".mro_shape_detector": ("FlextInfraMROShapeDetector",),
        ".namespace_source_detector": ("FlextInfraNamespaceSourceDetector",),
        ".pattern_smell_detector": ("FlextInfraPatternSmellDetector",),
        ".private_import_bypass_detector": ("FlextInfraPrivateImportBypassDetector",),
        ".runtime_alias_detector": ("FlextInfraRuntimeAliasDetector",),
        ".silent_failure_detector": ("FlextInfraSilentFailureDetector",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
