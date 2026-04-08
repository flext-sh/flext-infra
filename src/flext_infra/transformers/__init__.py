# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Transformers package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.transformers._base as _flext_infra_transformers__base

    _base = _flext_infra_transformers__base
    import flext_infra._utilities.import_normalizer as _flext_infra__utilities_import_normalizer
    from flext_infra.transformers._base import (
        FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer,
    )

    _utilities_normalizer = _flext_infra__utilities_import_normalizer
    import flext_infra.transformers.alias_remover as _flext_infra_transformers_alias_remover
    from flext_infra._utilities.import_normalizer import (
        FlextInfraNormalizerContext,
        FlextInfraUtilitiesImportNormalizer,
    )

    alias_remover = _flext_infra_transformers_alias_remover
    import flext_infra.transformers.census_visitors as _flext_infra_transformers_census_visitors
    from flext_infra.transformers.alias_remover import FlextInfraRefactorAliasRemover

    census_visitors = _flext_infra_transformers_census_visitors
    import flext_infra.transformers.class_nesting as _flext_infra_transformers_class_nesting
    from flext_infra.transformers.census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
    )

    class_nesting = _flext_infra_transformers_class_nesting
    import flext_infra.transformers.class_reconstructor as _flext_infra_transformers_class_reconstructor
    from flext_infra.transformers.class_nesting import (
        FlextInfraRefactorClassNestingTransformer,
    )

    class_reconstructor = _flext_infra_transformers_class_reconstructor
    import flext_infra.transformers.deprecated_remover as _flext_infra_transformers_deprecated_remover
    from flext_infra.transformers.class_reconstructor import (
        FlextInfraRefactorClassReconstructor,
    )

    deprecated_remover = _flext_infra_transformers_deprecated_remover
    import flext_infra.transformers.helper_consolidation as _flext_infra_transformers_helper_consolidation
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover,
    )

    helper_consolidation = _flext_infra_transformers_helper_consolidation
    import flext_infra.transformers.import_bypass_remover as _flext_infra_transformers_import_bypass_remover
    from flext_infra.transformers.helper_consolidation import (
        FlextInfraHelperConsolidationTransformer,
    )

    import_bypass_remover = _flext_infra_transformers_import_bypass_remover
    import flext_infra.transformers.import_modernizer as _flext_infra_transformers_import_modernizer
    from flext_infra.transformers.import_bypass_remover import (
        FlextInfraRefactorImportBypassRemover,
    )

    import_modernizer = _flext_infra_transformers_import_modernizer
    import flext_infra.transformers.lazy_import_fixer as _flext_infra_transformers_lazy_import_fixer
    from flext_infra.transformers.import_modernizer import (
        FlextInfraRefactorImportModernizer,
    )

    lazy_import_fixer = _flext_infra_transformers_lazy_import_fixer
    import flext_infra.transformers.mro_remover as _flext_infra_transformers_mro_remover
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer,
    )

    mro_remover = _flext_infra_transformers_mro_remover
    import flext_infra.transformers.mro_symbol_propagator as _flext_infra_transformers_mro_symbol_propagator
    from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover

    mro_symbol_propagator = _flext_infra_transformers_mro_symbol_propagator
    import flext_infra.transformers.nested_class_propagation as _flext_infra_transformers_nested_class_propagation
    from flext_infra.transformers.mro_symbol_propagator import (
        FlextInfraRefactorMROSymbolPropagator,
    )

    nested_class_propagation = _flext_infra_transformers_nested_class_propagation
    import flext_infra._utilities.transformer_policy as _flext_infra__utilities_transformer_policy
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer,
    )

    policy = _flext_infra__utilities_transformer_policy
    import flext_infra.transformers.signature_propagator as _flext_infra_transformers_signature_propagator
    from flext_infra._utilities.transformer_policy import (
        FlextInfraUtilitiesRefactorTransformerPolicy,
    )

    signature_propagator = _flext_infra_transformers_signature_propagator
    import flext_infra.transformers.symbol_propagator as _flext_infra_transformers_symbol_propagator
    from flext_infra.transformers.signature_propagator import (
        FlextInfraRefactorSignaturePropagator,
    )

    symbol_propagator = _flext_infra_transformers_symbol_propagator
    import flext_infra.transformers.tier0_import_fixer as _flext_infra_transformers_tier0_import_fixer
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator,
    )

    tier0_import_fixer = _flext_infra_transformers_tier0_import_fixer
    import flext_infra.transformers.typing_annotation_replacer as _flext_infra_transformers_typing_annotation_replacer
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer,
    )

    typing_annotation_replacer = _flext_infra_transformers_typing_annotation_replacer
    import flext_infra.transformers.typing_unifier as _flext_infra_transformers_typing_unifier
    from flext_infra.transformers.typing_annotation_replacer import (
        FlextInfraTypingAnnotationReplacer,
    )

    typing_unifier = _flext_infra_transformers_typing_unifier
    import flext_infra.transformers.violation_census_visitor as _flext_infra_transformers_violation_census_visitor
    from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier

    violation_census_visitor = _flext_infra_transformers_violation_census_visitor
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor,
    )
_LAZY_IMPORTS = {
    "FlextInfraCensusImportDiscoveryVisitor": (
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusImportDiscoveryVisitor",
    ),
    "FlextInfraCensusUsageCollector": (
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusUsageCollector",
    ),
    "FlextInfraChangeTrackingTransformer": (
        "flext_infra.transformers._base",
        "FlextInfraChangeTrackingTransformer",
    ),
    "FlextInfraHelperConsolidationTransformer": (
        "flext_infra.transformers.helper_consolidation",
        "FlextInfraHelperConsolidationTransformer",
    ),
    "FlextInfraNestedClassPropagationTransformer": (
        "flext_infra.transformers.nested_class_propagation",
        "FlextInfraNestedClassPropagationTransformer",
    ),
    "FlextInfraNormalizerContext": (
        "flext_infra._utilities.import_normalizer",
        "FlextInfraNormalizerContext",
    ),
    "FlextInfraRefactorAliasRemover": (
        "flext_infra.transformers.alias_remover",
        "FlextInfraRefactorAliasRemover",
    ),
    "FlextInfraRefactorClassNestingTransformer": (
        "flext_infra.transformers.class_nesting",
        "FlextInfraRefactorClassNestingTransformer",
    ),
    "FlextInfraRefactorClassReconstructor": (
        "flext_infra.transformers.class_reconstructor",
        "FlextInfraRefactorClassReconstructor",
    ),
    "FlextInfraRefactorDeprecatedRemover": (
        "flext_infra.transformers.deprecated_remover",
        "FlextInfraRefactorDeprecatedRemover",
    ),
    "FlextInfraRefactorImportBypassRemover": (
        "flext_infra.transformers.import_bypass_remover",
        "FlextInfraRefactorImportBypassRemover",
    ),
    "FlextInfraRefactorImportModernizer": (
        "flext_infra.transformers.import_modernizer",
        "FlextInfraRefactorImportModernizer",
    ),
    "FlextInfraRefactorLazyImportFixer": (
        "flext_infra.transformers.lazy_import_fixer",
        "FlextInfraRefactorLazyImportFixer",
    ),
    "FlextInfraRefactorMRORemover": (
        "flext_infra.transformers.mro_remover",
        "FlextInfraRefactorMRORemover",
    ),
    "FlextInfraRefactorMROSymbolPropagator": (
        "flext_infra.transformers.mro_symbol_propagator",
        "FlextInfraRefactorMROSymbolPropagator",
    ),
    "FlextInfraRefactorSignaturePropagator": (
        "flext_infra.transformers.signature_propagator",
        "FlextInfraRefactorSignaturePropagator",
    ),
    "FlextInfraRefactorSymbolPropagator": (
        "flext_infra.transformers.symbol_propagator",
        "FlextInfraRefactorSymbolPropagator",
    ),
    "FlextInfraUtilitiesRefactorTransformerPolicy": (
        "flext_infra._utilities.transformer_policy",
        "FlextInfraUtilitiesRefactorTransformerPolicy",
    ),
    "FlextInfraRefactorTypingUnifier": (
        "flext_infra.transformers.typing_unifier",
        "FlextInfraRefactorTypingUnifier",
    ),
    "FlextInfraRopeTransformer": (
        "flext_infra.transformers._base",
        "FlextInfraRopeTransformer",
    ),
    "FlextInfraTransformerTier0ImportFixer": (
        "flext_infra.transformers.tier0_import_fixer",
        "FlextInfraTransformerTier0ImportFixer",
    ),
    "FlextInfraTypingAnnotationReplacer": (
        "flext_infra.transformers.typing_annotation_replacer",
        "FlextInfraTypingAnnotationReplacer",
    ),
    "FlextInfraUtilitiesImportNormalizer": (
        "flext_infra._utilities.import_normalizer",
        "FlextInfraUtilitiesImportNormalizer",
    ),
    "FlextInfraViolationCensusVisitor": (
        "flext_infra.transformers.violation_census_visitor",
        "FlextInfraViolationCensusVisitor",
    ),
    "_base": "flext_infra.transformers._base",
    "_utilities_normalizer": "flext_infra._utilities.import_normalizer",
    "alias_remover": "flext_infra.transformers.alias_remover",
    "census_visitors": "flext_infra.transformers.census_visitors",
    "class_nesting": "flext_infra.transformers.class_nesting",
    "class_reconstructor": "flext_infra.transformers.class_reconstructor",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "deprecated_remover": "flext_infra.transformers.deprecated_remover",
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "helper_consolidation": "flext_infra.transformers.helper_consolidation",
    "import_bypass_remover": "flext_infra.transformers.import_bypass_remover",
    "import_modernizer": "flext_infra.transformers.import_modernizer",
    "lazy_import_fixer": "flext_infra.transformers.lazy_import_fixer",
    "mro_remover": "flext_infra.transformers.mro_remover",
    "mro_symbol_propagator": "flext_infra.transformers.mro_symbol_propagator",
    "nested_class_propagation": "flext_infra.transformers.nested_class_propagation",
    "policy": "flext_infra._utilities.transformer_policy",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "signature_propagator": "flext_infra.transformers.signature_propagator",
    "symbol_propagator": "flext_infra.transformers.symbol_propagator",
    "tier0_import_fixer": "flext_infra.transformers.tier0_import_fixer",
    "typing_annotation_replacer": "flext_infra.transformers.typing_annotation_replacer",
    "typing_unifier": "flext_infra.transformers.typing_unifier",
    "violation_census_visitor": "flext_infra.transformers.violation_census_visitor",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraNormalizerContext",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraRopeTransformer",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypingAnnotationReplacer",
    "FlextInfraUtilitiesImportNormalizer",
    "FlextInfraUtilitiesRefactorTransformerPolicy",
    "FlextInfraViolationCensusVisitor",
    "_base",
    "_utilities_normalizer",
    "alias_remover",
    "census_visitors",
    "class_nesting",
    "class_reconstructor",
    "d",
    "deprecated_remover",
    "e",
    "h",
    "helper_consolidation",
    "import_bypass_remover",
    "import_modernizer",
    "lazy_import_fixer",
    "mro_remover",
    "mro_symbol_propagator",
    "nested_class_propagation",
    "policy",
    "r",
    "s",
    "signature_propagator",
    "symbol_propagator",
    "tier0_import_fixer",
    "typing_annotation_replacer",
    "typing_unifier",
    "violation_census_visitor",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
