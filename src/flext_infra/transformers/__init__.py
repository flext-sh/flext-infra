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
    from flext_infra import (
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
    from flext_infra.alias_remover import FlextInfraRefactorAliasRemover
    from flext_infra.census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
    )
    from flext_infra.class_nesting import FlextInfraRefactorClassNestingTransformer
    from flext_infra.class_reconstructor import FlextInfraRefactorClassReconstructor
    from flext_infra.deprecated_remover import FlextInfraRefactorDeprecatedRemover
    from flext_infra.dict_to_mapping import FlextInfraDictToMappingTransformer
    from flext_infra.helper_consolidation import (
        FlextInfraHelperConsolidationTransformer,
    )
    from flext_infra.import_bypass_remover import FlextInfraRefactorImportBypassRemover
    from flext_infra.import_modernizer import FlextInfraRefactorImportModernizer
    from flext_infra.lazy_import_fixer import FlextInfraRefactorLazyImportFixer
    from flext_infra.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer,
    )
    from flext_infra.mro_remover import FlextInfraRefactorMRORemover
    from flext_infra.mro_symbol_propagator import FlextInfraRefactorMROSymbolPropagator
    from flext_infra.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer,
    )
    from flext_infra.policy import FlextInfraRefactorTransformerPolicyUtilities
    from flext_infra.redundant_cast_remover import FlextInfraRedundantCastRemover
    from flext_infra.signature_propagator import FlextInfraRefactorSignaturePropagator
    from flext_infra.symbol_propagator import FlextInfraRefactorSymbolPropagator
    from flext_infra.tier0_import_fixer import FlextInfraTransformerTier0ImportFixer
    from flext_infra.typing_annotation_replacer import (
        FlextInfraTypingAnnotationReplacer,
    )
    from flext_infra.typing_unifier import FlextInfraRefactorTypingUnifier
    from flext_infra.violation_census_visitor import FlextInfraViolationCensusVisitor

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraCensusImportDiscoveryVisitor": "flext_infra.census_visitors",
    "FlextInfraCensusUsageCollector": "flext_infra.census_visitors",
    "FlextInfraDictToMappingTransformer": "flext_infra.dict_to_mapping",
    "FlextInfraHelperConsolidationTransformer": "flext_infra.helper_consolidation",
    "FlextInfraNestedClassPropagationTransformer": "flext_infra.nested_class_propagation",
    "FlextInfraRedundantCastRemover": "flext_infra.redundant_cast_remover",
    "FlextInfraRefactorAliasRemover": "flext_infra.alias_remover",
    "FlextInfraRefactorClassNestingTransformer": "flext_infra.class_nesting",
    "FlextInfraRefactorClassReconstructor": "flext_infra.class_reconstructor",
    "FlextInfraRefactorDeprecatedRemover": "flext_infra.deprecated_remover",
    "FlextInfraRefactorImportBypassRemover": "flext_infra.import_bypass_remover",
    "FlextInfraRefactorImportModernizer": "flext_infra.import_modernizer",
    "FlextInfraRefactorLazyImportFixer": "flext_infra.lazy_import_fixer",
    "FlextInfraRefactorMROPrivateInlineTransformer": "flext_infra.mro_private_inline",
    "FlextInfraRefactorMROQualifiedReferenceTransformer": "flext_infra.mro_private_inline",
    "FlextInfraRefactorMRORemover": "flext_infra.mro_remover",
    "FlextInfraRefactorMROSymbolPropagator": "flext_infra.mro_symbol_propagator",
    "FlextInfraRefactorSignaturePropagator": "flext_infra.signature_propagator",
    "FlextInfraRefactorSymbolPropagator": "flext_infra.symbol_propagator",
    "FlextInfraRefactorTransformerPolicyUtilities": "flext_infra.policy",
    "FlextInfraRefactorTypingUnifier": "flext_infra.typing_unifier",
    "FlextInfraTransformerTier0ImportFixer": "flext_infra.tier0_import_fixer",
    "FlextInfraTypingAnnotationReplacer": "flext_infra.typing_annotation_replacer",
    "FlextInfraViolationCensusVisitor": "flext_infra.violation_census_visitor",
    "alias_remover": "flext_infra.alias_remover",
    "census_visitors": "flext_infra.census_visitors",
    "class_nesting": "flext_infra.class_nesting",
    "class_reconstructor": "flext_infra.class_reconstructor",
    "deprecated_remover": "flext_infra.deprecated_remover",
    "dict_to_mapping": "flext_infra.dict_to_mapping",
    "helper_consolidation": "flext_infra.helper_consolidation",
    "import_bypass_remover": "flext_infra.import_bypass_remover",
    "import_modernizer": "flext_infra.import_modernizer",
    "lazy_import_fixer": "flext_infra.lazy_import_fixer",
    "mro_private_inline": "flext_infra.mro_private_inline",
    "mro_remover": "flext_infra.mro_remover",
    "mro_symbol_propagator": "flext_infra.mro_symbol_propagator",
    "nested_class_propagation": "flext_infra.nested_class_propagation",
    "policy": "flext_infra.policy",
    "redundant_cast_remover": "flext_infra.redundant_cast_remover",
    "signature_propagator": "flext_infra.signature_propagator",
    "symbol_propagator": "flext_infra.symbol_propagator",
    "tier0_import_fixer": "flext_infra.tier0_import_fixer",
    "typing_annotation_replacer": "flext_infra.typing_annotation_replacer",
    "typing_unifier": "flext_infra.typing_unifier",
    "violation_census_visitor": "flext_infra.violation_census_visitor",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
