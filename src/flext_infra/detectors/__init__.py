# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.detectors package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.detectors.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.detectors.class_placement_detector import (
        FlextInfraClassPlacementDetector as FlextInfraClassPlacementDetector,
    )
    from flext_infra.detectors.compatibility_alias_detector import (
        FlextInfraCompatibilityAliasDetector as FlextInfraCompatibilityAliasDetector,
    )
    from flext_infra.detectors.cyclic_import_detector import (
        FlextInfraCyclicImportDetector as FlextInfraCyclicImportDetector,
    )
    from flext_infra.detectors.facade_scanner import (
        FlextInfraScanner as FlextInfraScanner,
    )
    from flext_infra.detectors.future_annotations_detector import (
        FlextInfraFutureAnnotationsDetector as FlextInfraFutureAnnotationsDetector,
    )
    from flext_infra.detectors.import_alias_detector import (
        FlextInfraImportAliasDetector as FlextInfraImportAliasDetector,
    )
    from flext_infra.detectors.inline_import_detector import (
        FlextInfraInlineImportDetector as FlextInfraInlineImportDetector,
    )
    from flext_infra.detectors.internal_import_detector import (
        FlextInfraInternalImportDetector as FlextInfraInternalImportDetector,
    )
    from flext_infra.detectors.loose_object_detector import (
        FlextInfraLooseObjectDetector as FlextInfraLooseObjectDetector,
    )
    from flext_infra.detectors.loose_test_function_detector import (
        FlextInfraLooseTestFunctionDetector as FlextInfraLooseTestFunctionDetector,
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
    from flext_infra.detectors.mro_shape_detector import (
        FlextInfraMROShapeDetector as FlextInfraMROShapeDetector,
    )
    from flext_infra.detectors.namespace_source_detector import (
        FlextInfraNamespaceSourceDetector as FlextInfraNamespaceSourceDetector,
    )
    from flext_infra.detectors.pattern_smell_detector import (
        FlextInfraPatternSmellDetector as FlextInfraPatternSmellDetector,
    )
    from flext_infra.detectors.private_import_bypass_detector import (
        FlextInfraPrivateImportBypassDetector as FlextInfraPrivateImportBypassDetector,
    )
    from flext_infra.detectors.runtime_alias_detector import (
        FlextInfraRuntimeAliasDetector as FlextInfraRuntimeAliasDetector,
    )
    from flext_infra.detectors.silent_failure_detector import (
        FlextInfraSilentFailureDetector as FlextInfraSilentFailureDetector,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
