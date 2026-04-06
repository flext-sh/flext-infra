# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Detectors package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.detectors._base_detector as _flext_infra_detectors__base_detector

    _base_detector = _flext_infra_detectors__base_detector
    import flext_infra.detectors.class_placement_detector as _flext_infra_detectors_class_placement_detector
    from flext_infra.detectors._base_detector import (
        DetectorContext,
        FlextInfraScanFileMixin,
    )

    class_placement_detector = _flext_infra_detectors_class_placement_detector
    import flext_infra.detectors.compatibility_alias_detector as _flext_infra_detectors_compatibility_alias_detector
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector,
    )

    compatibility_alias_detector = _flext_infra_detectors_compatibility_alias_detector
    import flext_infra.detectors.cyclic_import_detector as _flext_infra_detectors_cyclic_import_detector
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector,
    )

    cyclic_import_detector = _flext_infra_detectors_cyclic_import_detector
    import flext_infra.detectors.future_annotations_detector as _flext_infra_detectors_future_annotations_detector
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector,
    )

    future_annotations_detector = _flext_infra_detectors_future_annotations_detector
    import flext_infra.detectors.import_alias_detector as _flext_infra_detectors_import_alias_detector
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector,
    )

    import_alias_detector = _flext_infra_detectors_import_alias_detector
    import flext_infra.detectors.internal_import_detector as _flext_infra_detectors_internal_import_detector
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector,
    )

    internal_import_detector = _flext_infra_detectors_internal_import_detector
    import flext_infra.detectors.loose_object_detector as _flext_infra_detectors_loose_object_detector
    from flext_infra.detectors.internal_import_detector import (
        FlextInfraInternalImportDetector,
    )

    loose_object_detector = _flext_infra_detectors_loose_object_detector
    import flext_infra.detectors.manual_protocol_detector as _flext_infra_detectors_manual_protocol_detector
    from flext_infra.detectors.loose_object_detector import (
        FlextInfraLooseObjectDetector,
    )

    manual_protocol_detector = _flext_infra_detectors_manual_protocol_detector
    import flext_infra.detectors.manual_typing_alias_detector as _flext_infra_detectors_manual_typing_alias_detector
    from flext_infra.detectors.manual_protocol_detector import (
        FlextInfraManualProtocolDetector,
    )

    manual_typing_alias_detector = _flext_infra_detectors_manual_typing_alias_detector
    import flext_infra.detectors.mro_completeness_detector as _flext_infra_detectors_mro_completeness_detector
    from flext_infra.detectors.manual_typing_alias_detector import (
        FlextInfraManualTypingAliasDetector,
    )

    mro_completeness_detector = _flext_infra_detectors_mro_completeness_detector
    import flext_infra.detectors.namespace_facade_scanner as _flext_infra_detectors_namespace_facade_scanner
    from flext_infra.detectors.mro_completeness_detector import (
        FlextInfraMROCompletenessDetector,
    )

    namespace_facade_scanner = _flext_infra_detectors_namespace_facade_scanner
    import flext_infra.detectors.namespace_source_detector as _flext_infra_detectors_namespace_source_detector
    from flext_infra.detectors.namespace_facade_scanner import (
        FlextInfraNamespaceFacadeScanner,
    )

    namespace_source_detector = _flext_infra_detectors_namespace_source_detector
    import flext_infra.detectors.runtime_alias_detector as _flext_infra_detectors_runtime_alias_detector
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector,
    )

    runtime_alias_detector = _flext_infra_detectors_runtime_alias_detector
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector,
    )
_LAZY_IMPORTS = {
    "DetectorContext": "flext_infra.detectors._base_detector",
    "FlextInfraClassPlacementDetector": "flext_infra.detectors.class_placement_detector",
    "FlextInfraCompatibilityAliasDetector": "flext_infra.detectors.compatibility_alias_detector",
    "FlextInfraCyclicImportDetector": "flext_infra.detectors.cyclic_import_detector",
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
    "c": ("flext_core.constants", "FlextConstants"),
    "class_placement_detector": "flext_infra.detectors.class_placement_detector",
    "compatibility_alias_detector": "flext_infra.detectors.compatibility_alias_detector",
    "cyclic_import_detector": "flext_infra.detectors.cyclic_import_detector",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "future_annotations_detector": "flext_infra.detectors.future_annotations_detector",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "import_alias_detector": "flext_infra.detectors.import_alias_detector",
    "internal_import_detector": "flext_infra.detectors.internal_import_detector",
    "loose_object_detector": "flext_infra.detectors.loose_object_detector",
    "m": ("flext_core.models", "FlextModels"),
    "manual_protocol_detector": "flext_infra.detectors.manual_protocol_detector",
    "manual_typing_alias_detector": "flext_infra.detectors.manual_typing_alias_detector",
    "mro_completeness_detector": "flext_infra.detectors.mro_completeness_detector",
    "namespace_facade_scanner": "flext_infra.detectors.namespace_facade_scanner",
    "namespace_source_detector": "flext_infra.detectors.namespace_source_detector",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "runtime_alias_detector": "flext_infra.detectors.runtime_alias_detector",
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "DetectorContext",
    "FlextInfraClassPlacementDetector",
    "FlextInfraCompatibilityAliasDetector",
    "FlextInfraCyclicImportDetector",
    "FlextInfraFutureAnnotationsDetector",
    "FlextInfraImportAliasDetector",
    "FlextInfraInternalImportDetector",
    "FlextInfraLooseObjectDetector",
    "FlextInfraMROCompletenessDetector",
    "FlextInfraManualProtocolDetector",
    "FlextInfraManualTypingAliasDetector",
    "FlextInfraNamespaceFacadeScanner",
    "FlextInfraNamespaceSourceDetector",
    "FlextInfraRuntimeAliasDetector",
    "FlextInfraScanFileMixin",
    "_base_detector",
    "c",
    "class_placement_detector",
    "compatibility_alias_detector",
    "cyclic_import_detector",
    "d",
    "e",
    "future_annotations_detector",
    "h",
    "import_alias_detector",
    "internal_import_detector",
    "loose_object_detector",
    "m",
    "manual_protocol_detector",
    "manual_typing_alias_detector",
    "mro_completeness_detector",
    "namespace_facade_scanner",
    "namespace_source_detector",
    "p",
    "r",
    "runtime_alias_detector",
    "s",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
