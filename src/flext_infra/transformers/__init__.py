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
    import flext_infra.transformers._utilities_normalizer as _flext_infra_transformers__utilities_normalizer
    from flext_infra.transformers._base import (
        FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer,
    )

    _utilities_normalizer = _flext_infra_transformers__utilities_normalizer
    import flext_infra.transformers.alias_remover as _flext_infra_transformers_alias_remover
    from flext_infra.transformers._utilities_normalizer import (
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
    import flext_infra.transformers.dict_to_mapping as _flext_infra_transformers_dict_to_mapping
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover,
    )

    dict_to_mapping = _flext_infra_transformers_dict_to_mapping
    import flext_infra.transformers.helper_consolidation as _flext_infra_transformers_helper_consolidation
    from flext_infra.transformers.dict_to_mapping import (
        FlextInfraDictToMappingTransformer,
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
    import flext_infra.transformers.mro_private_inline as _flext_infra_transformers_mro_private_inline
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer,
    )

    mro_private_inline = _flext_infra_transformers_mro_private_inline
    import flext_infra.transformers.mro_remover as _flext_infra_transformers_mro_remover
    from flext_infra.transformers.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer,
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
    import flext_infra.transformers.policy as _flext_infra_transformers_policy
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer,
    )

    policy = _flext_infra_transformers_policy
    import flext_infra.transformers.redundant_cast_remover as _flext_infra_transformers_redundant_cast_remover
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities,
    )

    redundant_cast_remover = _flext_infra_transformers_redundant_cast_remover
    import flext_infra.transformers.signature_propagator as _flext_infra_transformers_signature_propagator
    from flext_infra.transformers.redundant_cast_remover import (
        FlextInfraRedundantCastRemover,
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
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor,
    )
_LAZY_IMPORTS = {
    "FlextInfraCensusImportDiscoveryVisitor": "flext_infra.transformers.census_visitors",
    "FlextInfraCensusUsageCollector": "flext_infra.transformers.census_visitors",
    "FlextInfraChangeTrackingTransformer": "flext_infra.transformers._base",
    "FlextInfraDictToMappingTransformer": "flext_infra.transformers.dict_to_mapping",
    "FlextInfraHelperConsolidationTransformer": "flext_infra.transformers.helper_consolidation",
    "FlextInfraNestedClassPropagationTransformer": "flext_infra.transformers.nested_class_propagation",
    "FlextInfraNormalizerContext": "flext_infra.transformers._utilities_normalizer",
    "FlextInfraRedundantCastRemover": "flext_infra.transformers.redundant_cast_remover",
    "FlextInfraRefactorAliasRemover": "flext_infra.transformers.alias_remover",
    "FlextInfraRefactorClassNestingTransformer": "flext_infra.transformers.class_nesting",
    "FlextInfraRefactorClassReconstructor": "flext_infra.transformers.class_reconstructor",
    "FlextInfraRefactorDeprecatedRemover": "flext_infra.transformers.deprecated_remover",
    "FlextInfraRefactorImportBypassRemover": "flext_infra.transformers.import_bypass_remover",
    "FlextInfraRefactorImportModernizer": "flext_infra.transformers.import_modernizer",
    "FlextInfraRefactorLazyImportFixer": "flext_infra.transformers.lazy_import_fixer",
    "FlextInfraRefactorMROPrivateInlineTransformer": "flext_infra.transformers.mro_private_inline",
    "FlextInfraRefactorMROQualifiedReferenceTransformer": "flext_infra.transformers.mro_private_inline",
    "FlextInfraRefactorMRORemover": "flext_infra.transformers.mro_remover",
    "FlextInfraRefactorMROSymbolPropagator": "flext_infra.transformers.mro_symbol_propagator",
    "FlextInfraRefactorSignaturePropagator": "flext_infra.transformers.signature_propagator",
    "FlextInfraRefactorSymbolPropagator": "flext_infra.transformers.symbol_propagator",
    "FlextInfraRefactorTransformerPolicyUtilities": "flext_infra.transformers.policy",
    "FlextInfraRefactorTypingUnifier": "flext_infra.transformers.typing_unifier",
    "FlextInfraRopeTransformer": "flext_infra.transformers._base",
    "FlextInfraTransformerTier0ImportFixer": "flext_infra.transformers.tier0_import_fixer",
    "FlextInfraTypingAnnotationReplacer": "flext_infra.transformers.typing_annotation_replacer",
    "FlextInfraUtilitiesImportNormalizer": "flext_infra.transformers._utilities_normalizer",
    "FlextInfraViolationCensusVisitor": "flext_infra.transformers.violation_census_visitor",
    "_base": "flext_infra.transformers._base",
    "_utilities_normalizer": "flext_infra.transformers._utilities_normalizer",
    "alias_remover": "flext_infra.transformers.alias_remover",
    "c": ("flext_core.constants", "FlextConstants"),
    "census_visitors": "flext_infra.transformers.census_visitors",
    "class_nesting": "flext_infra.transformers.class_nesting",
    "class_reconstructor": "flext_infra.transformers.class_reconstructor",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "deprecated_remover": "flext_infra.transformers.deprecated_remover",
    "dict_to_mapping": "flext_infra.transformers.dict_to_mapping",
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "helper_consolidation": "flext_infra.transformers.helper_consolidation",
    "import_bypass_remover": "flext_infra.transformers.import_bypass_remover",
    "import_modernizer": "flext_infra.transformers.import_modernizer",
    "lazy_import_fixer": "flext_infra.transformers.lazy_import_fixer",
    "m": ("flext_core.models", "FlextModels"),
    "mro_private_inline": "flext_infra.transformers.mro_private_inline",
    "mro_remover": "flext_infra.transformers.mro_remover",
    "mro_symbol_propagator": "flext_infra.transformers.mro_symbol_propagator",
    "nested_class_propagation": "flext_infra.transformers.nested_class_propagation",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "policy": "flext_infra.transformers.policy",
    "r": ("flext_core.result", "FlextResult"),
    "redundant_cast_remover": "flext_infra.transformers.redundant_cast_remover",
    "s": ("flext_core.service", "FlextService"),
    "signature_propagator": "flext_infra.transformers.signature_propagator",
    "symbol_propagator": "flext_infra.transformers.symbol_propagator",
    "t": ("flext_core.typings", "FlextTypes"),
    "tier0_import_fixer": "flext_infra.transformers.tier0_import_fixer",
    "typing_annotation_replacer": "flext_infra.transformers.typing_annotation_replacer",
    "typing_unifier": "flext_infra.transformers.typing_unifier",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "violation_census_visitor": "flext_infra.transformers.violation_census_visitor",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraDictToMappingTransformer",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraNormalizerContext",
    "FlextInfraRedundantCastRemover",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorMROPrivateInlineTransformer",
    "FlextInfraRefactorMROQualifiedReferenceTransformer",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTransformerPolicyUtilities",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraRopeTransformer",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypingAnnotationReplacer",
    "FlextInfraUtilitiesImportNormalizer",
    "FlextInfraViolationCensusVisitor",
    "_base",
    "_utilities_normalizer",
    "alias_remover",
    "c",
    "census_visitors",
    "class_nesting",
    "class_reconstructor",
    "d",
    "deprecated_remover",
    "dict_to_mapping",
    "e",
    "h",
    "helper_consolidation",
    "import_bypass_remover",
    "import_modernizer",
    "lazy_import_fixer",
    "m",
    "mro_private_inline",
    "mro_remover",
    "mro_symbol_propagator",
    "nested_class_propagation",
    "p",
    "policy",
    "r",
    "redundant_cast_remover",
    "s",
    "signature_propagator",
    "symbol_propagator",
    "t",
    "tier0_import_fixer",
    "typing_annotation_replacer",
    "typing_unifier",
    "u",
    "violation_census_visitor",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
