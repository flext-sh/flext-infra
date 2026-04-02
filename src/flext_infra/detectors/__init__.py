# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Detectors package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.detectors import (
        _base_detector,
        class_placement_detector,
        compatibility_alias_detector,
        cyclic_import_detector,
        dependency_analyzer_base,
        future_annotations_detector,
        import_alias_detector,
        internal_import_detector,
        loose_object_detector,
        manual_protocol_detector,
        manual_typing_alias_detector,
        mro_completeness_detector,
        namespace_facade_scanner,
        namespace_source_detector,
        runtime_alias_detector,
    )
    from flext_infra.detectors._base_detector import (
        DetectorContext,
        FlextInfraScanFileMixin,
    )
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector,
    )
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector,
    )
    from flext_infra.detectors.dependency_analyzer_base import (
        FlextInfraDependencyAnalyzer,
    )
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector,
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
    from flext_infra.detectors.namespace_facade_scanner import (
        FlextInfraNamespaceFacadeScanner,
    )
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "DetectorContext": "flext_infra.detectors._base_detector",
    "FlextInfraClassPlacementDetector": "flext_infra.detectors.class_placement_detector",
    "FlextInfraCompatibilityAliasDetector": "flext_infra.detectors.compatibility_alias_detector",
    "FlextInfraCyclicImportDetector": "flext_infra.detectors.cyclic_import_detector",
    "FlextInfraDependencyAnalyzer": "flext_infra.detectors.dependency_analyzer_base",
    "FlextInfraFutureAnnotationsDetector": "flext_infra.detectors.future_annotations_detector",
    "FlextInfraImportAliasDetector": "flext_infra.detectors.import_alias_detector",
    "FlextInfraInternalImportDetector": "flext_infra.detectors.internal_import_detector",
    "FlextInfraLooseObjectDetector": "flext_infra.detectors.loose_object_detector",
    "FlextInfraMROCompletenessDetector": "flext_infra.detectors.mro_completeness_detector",
    "FlextInfraManualProtocolDetector": "flext_infra.detectors.manual_protocol_detector",
    "FlextInfraManualTypingAliasDetector": "flext_infra.detectors.manual_typing_alias_detector",
    "FlextInfraNamespaceFacadeScanner": "flext_infra.detectors.namespace_facade_scanner",
    "FlextInfraNamespaceSourceDetector": "flext_infra.detectors.namespace_source_detector",
    "FlextInfraRuntimeAliasDetector": "flext_infra.detectors.runtime_alias_detector",
    "FlextInfraScanFileMixin": "flext_infra.detectors._base_detector",
    "_base_detector": "flext_infra.detectors._base_detector",
    "class_placement_detector": "flext_infra.detectors.class_placement_detector",
    "compatibility_alias_detector": "flext_infra.detectors.compatibility_alias_detector",
    "cyclic_import_detector": "flext_infra.detectors.cyclic_import_detector",
    "dependency_analyzer_base": "flext_infra.detectors.dependency_analyzer_base",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
