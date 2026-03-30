# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Detectors package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.detectors import (
        class_placement_detector as class_placement_detector,
        compatibility_alias_detector as compatibility_alias_detector,
        cyclic_import_detector as cyclic_import_detector,
        dependency_analyzer_base as dependency_analyzer_base,
        future_annotations_detector as future_annotations_detector,
        import_alias_detector as import_alias_detector,
        import_collector as import_collector,
        internal_import_detector as internal_import_detector,
        loose_object_detector as loose_object_detector,
        manual_protocol_detector as manual_protocol_detector,
        manual_typing_alias_detector as manual_typing_alias_detector,
        mro_completeness_detector as mro_completeness_detector,
        namespace_facade_scanner as namespace_facade_scanner,
        namespace_source_detector as namespace_source_detector,
        runtime_alias_detector as runtime_alias_detector,
    )
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector as FlextInfraClassPlacementDetector,
    )
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector as FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector as FlextInfraCyclicImportDetector,
    )
    from flext_infra.detectors.dependency_analyzer_base import (
        FlextInfraDependencyAnalyzer as FlextInfraDependencyAnalyzer,
    )
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector as FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector as FlextInfraImportAliasDetector,
    )
    from flext_infra.detectors.import_collector import (
        FlextInfraImportCollector as FlextInfraImportCollector,
    )
    from flext_infra.detectors.internal_import_detector import (
        FlextInfraInternalImportDetector as FlextInfraInternalImportDetector,
    )
    from flext_infra.detectors.loose_object_detector import (
        FlextInfraLooseObjectDetector as FlextInfraLooseObjectDetector,
    )
    from flext_infra.detectors.manual_protocol_detector import (
        FlextInfraManualProtocolDetector as FlextInfraManualProtocolDetector,
    )
    from flext_infra.detectors.manual_typing_alias_detector import (
        FlextInfraManualTypingAliasDetector as FlextInfraManualTypingAliasDetector,
    )
    from flext_infra.detectors.mro_completeness_detector import (
        FlextInfraMROCompletenessDetector as FlextInfraMROCompletenessDetector,
    )
    from flext_infra.detectors.namespace_facade_scanner import (
        FlextInfraNamespaceFacadeScanner as FlextInfraNamespaceFacadeScanner,
    )
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector as FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector as FlextInfraRuntimeAliasDetector,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraClassPlacementDetector": [
        "flext_infra.detectors.class_placement_detector",
        "FlextInfraClassPlacementDetector",
    ],
    "FlextInfraCompatibilityAliasDetector": [
        "flext_infra.detectors.compatibility_alias_detector",
        "FlextInfraCompatibilityAliasDetector",
    ],
    "FlextInfraCyclicImportDetector": [
        "flext_infra.detectors.cyclic_import_detector",
        "FlextInfraCyclicImportDetector",
    ],
    "FlextInfraDependencyAnalyzer": [
        "flext_infra.detectors.dependency_analyzer_base",
        "FlextInfraDependencyAnalyzer",
    ],
    "FlextInfraFutureAnnotationsDetector": [
        "flext_infra.detectors.future_annotations_detector",
        "FlextInfraFutureAnnotationsDetector",
    ],
    "FlextInfraImportAliasDetector": [
        "flext_infra.detectors.import_alias_detector",
        "FlextInfraImportAliasDetector",
    ],
    "FlextInfraImportCollector": [
        "flext_infra.detectors.import_collector",
        "FlextInfraImportCollector",
    ],
    "FlextInfraInternalImportDetector": [
        "flext_infra.detectors.internal_import_detector",
        "FlextInfraInternalImportDetector",
    ],
    "FlextInfraLooseObjectDetector": [
        "flext_infra.detectors.loose_object_detector",
        "FlextInfraLooseObjectDetector",
    ],
    "FlextInfraMROCompletenessDetector": [
        "flext_infra.detectors.mro_completeness_detector",
        "FlextInfraMROCompletenessDetector",
    ],
    "FlextInfraManualProtocolDetector": [
        "flext_infra.detectors.manual_protocol_detector",
        "FlextInfraManualProtocolDetector",
    ],
    "FlextInfraManualTypingAliasDetector": [
        "flext_infra.detectors.manual_typing_alias_detector",
        "FlextInfraManualTypingAliasDetector",
    ],
    "FlextInfraNamespaceFacadeScanner": [
        "flext_infra.detectors.namespace_facade_scanner",
        "FlextInfraNamespaceFacadeScanner",
    ],
    "FlextInfraNamespaceSourceDetector": [
        "flext_infra.detectors.namespace_source_detector",
        "FlextInfraNamespaceSourceDetector",
    ],
    "FlextInfraRuntimeAliasDetector": [
        "flext_infra.detectors.runtime_alias_detector",
        "FlextInfraRuntimeAliasDetector",
    ],
    "class_placement_detector": ["flext_infra.detectors.class_placement_detector", ""],
    "compatibility_alias_detector": [
        "flext_infra.detectors.compatibility_alias_detector",
        "",
    ],
    "cyclic_import_detector": ["flext_infra.detectors.cyclic_import_detector", ""],
    "dependency_analyzer_base": ["flext_infra.detectors.dependency_analyzer_base", ""],
    "future_annotations_detector": [
        "flext_infra.detectors.future_annotations_detector",
        "",
    ],
    "import_alias_detector": ["flext_infra.detectors.import_alias_detector", ""],
    "import_collector": ["flext_infra.detectors.import_collector", ""],
    "internal_import_detector": ["flext_infra.detectors.internal_import_detector", ""],
    "loose_object_detector": ["flext_infra.detectors.loose_object_detector", ""],
    "manual_protocol_detector": ["flext_infra.detectors.manual_protocol_detector", ""],
    "manual_typing_alias_detector": [
        "flext_infra.detectors.manual_typing_alias_detector",
        "",
    ],
    "mro_completeness_detector": [
        "flext_infra.detectors.mro_completeness_detector",
        "",
    ],
    "namespace_facade_scanner": ["flext_infra.detectors.namespace_facade_scanner", ""],
    "namespace_source_detector": [
        "flext_infra.detectors.namespace_source_detector",
        "",
    ],
    "runtime_alias_detector": ["flext_infra.detectors.runtime_alias_detector", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraClassPlacementDetector",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraCyclicImportDetector",
    "FlextInfraDependencyAnalyzer",
    "FlextInfraFutureAnnotationsDetector",
    "FlextInfraImportAliasDetector",
    "FlextInfraImportCollector",
    "FlextInfraInternalImportDetector",
    "FlextInfraLooseObjectDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraNamespaceFacadeScanner",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraRuntimeAliasDetector",
    "class_placement_detector",
    "compatibility_alias_detector",
    "cyclic_import_detector",
    "dependency_analyzer_base",
    "future_annotations_detector",
    "import_alias_detector",
    "import_collector",
    "internal_import_detector",
    "loose_object_detector",
    "manual_protocol_detector",
    "manual_typing_alias_detector",
    "mro_completeness_detector",
    "namespace_facade_scanner",
    "namespace_source_detector",
    "runtime_alias_detector",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
