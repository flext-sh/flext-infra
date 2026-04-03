# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Transformers package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.transformers import (
        _base,
        _utilities_normalizer,
        alias_remover,
        census_visitors,
        class_nesting,
        class_reconstructor,
        deprecated_remover,
        dict_to_mapping,
        helper_consolidation,
        import_bypass_remover,
        import_modernizer,
        lazy_import_fixer,
        mro_private_inline,
        mro_remover,
        mro_symbol_propagator,
        nested_class_propagation,
        policy,
        redundant_cast_remover,
        signature_propagator,
        symbol_propagator,
        tier0_import_fixer,
        typing_annotation_replacer,
        typing_unifier,
        violation_census_visitor,
    )
    from flext_infra.transformers._base import (
        FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer,
    )
    from flext_infra.transformers._utilities_normalizer import (
        FlextInfraNormalizerContext,
        FlextInfraUtilitiesImportNormalizer,
    )
    from flext_infra.transformers.alias_remover import FlextInfraRefactorAliasRemover
    from flext_infra.transformers.census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
    )
    from flext_infra.transformers.class_nesting import (
        FlextInfraRefactorClassNestingTransformer,
    )
    from flext_infra.transformers.class_reconstructor import (
        FlextInfraRefactorClassReconstructor,
    )
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover,
    )
    from flext_infra.transformers.dict_to_mapping import (
        FlextInfraDictToMappingTransformer,
    )
    from flext_infra.transformers.helper_consolidation import (
        FlextInfraHelperConsolidationTransformer,
    )
    from flext_infra.transformers.import_bypass_remover import (
        FlextInfraRefactorImportBypassRemover,
    )
    from flext_infra.transformers.import_modernizer import (
        FlextInfraRefactorImportModernizer,
    )
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer,
    )
    from flext_infra.transformers.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer,
    )
    from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
    from flext_infra.transformers.mro_symbol_propagator import (
        FlextInfraRefactorMROSymbolPropagator,
    )
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer,
    )
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities,
    )
    from flext_infra.transformers.redundant_cast_remover import (
        FlextInfraRedundantCastRemover,
    )
    from flext_infra.transformers.signature_propagator import (
        FlextInfraRefactorSignaturePropagator,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer,
    )
    from flext_infra.transformers.typing_annotation_replacer import (
        FlextInfraTypingAnnotationReplacer,
    )
    from flext_infra.transformers.typing_unifier import (
        FlextInfraRefactorTypingUnifier,
    )
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
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
    "census_visitors": "flext_infra.transformers.census_visitors",
    "class_nesting": "flext_infra.transformers.class_nesting",
    "class_reconstructor": "flext_infra.transformers.class_reconstructor",
    "deprecated_remover": "flext_infra.transformers.deprecated_remover",
    "dict_to_mapping": "flext_infra.transformers.dict_to_mapping",
    "helper_consolidation": "flext_infra.transformers.helper_consolidation",
    "import_bypass_remover": "flext_infra.transformers.import_bypass_remover",
    "import_modernizer": "flext_infra.transformers.import_modernizer",
    "lazy_import_fixer": "flext_infra.transformers.lazy_import_fixer",
    "mro_private_inline": "flext_infra.transformers.mro_private_inline",
    "mro_remover": "flext_infra.transformers.mro_remover",
    "mro_symbol_propagator": "flext_infra.transformers.mro_symbol_propagator",
    "nested_class_propagation": "flext_infra.transformers.nested_class_propagation",
    "policy": "flext_infra.transformers.policy",
    "redundant_cast_remover": "flext_infra.transformers.redundant_cast_remover",
    "signature_propagator": "flext_infra.transformers.signature_propagator",
    "symbol_propagator": "flext_infra.transformers.symbol_propagator",
    "tier0_import_fixer": "flext_infra.transformers.tier0_import_fixer",
    "typing_annotation_replacer": "flext_infra.transformers.typing_annotation_replacer",
    "typing_unifier": "flext_infra.transformers.typing_unifier",
    "violation_census_visitor": "flext_infra.transformers.violation_census_visitor",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
