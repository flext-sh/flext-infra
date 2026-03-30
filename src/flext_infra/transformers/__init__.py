# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Transformer classes for flext_infra.refactor."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.transformers import (
        alias_remover as alias_remover,
        census_visitors as census_visitors,
        class_nesting as class_nesting,
        class_reconstructor as class_reconstructor,
        deprecated_remover as deprecated_remover,
        dict_to_mapping as dict_to_mapping,
        helper_consolidation as helper_consolidation,
        import_bypass_remover as import_bypass_remover,
        import_modernizer as import_modernizer,
        lazy_import_fixer as lazy_import_fixer,
        mro_private_inline as mro_private_inline,
        mro_remover as mro_remover,
        mro_symbol_propagator as mro_symbol_propagator,
        nested_class_propagation as nested_class_propagation,
        policy as policy,
        redundant_cast_remover as redundant_cast_remover,
        signature_propagator as signature_propagator,
        symbol_propagator as symbol_propagator,
        tier0_import_fixer as tier0_import_fixer,
        typing_annotation_replacer as typing_annotation_replacer,
        typing_unifier as typing_unifier,
        violation_census_visitor as violation_census_visitor,
    )
    from flext_infra.transformers.alias_remover import (
        FlextInfraRefactorAliasRemover as FlextInfraRefactorAliasRemover,
    )
    from flext_infra.transformers.census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor as FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector as FlextInfraCensusUsageCollector,
    )
    from flext_infra.transformers.class_nesting import (
        FlextInfraRefactorClassNestingTransformer as FlextInfraRefactorClassNestingTransformer,
    )
    from flext_infra.transformers.class_reconstructor import (
        FlextInfraRefactorClassReconstructor as FlextInfraRefactorClassReconstructor,
    )
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover as FlextInfraRefactorDeprecatedRemover,
    )
    from flext_infra.transformers.dict_to_mapping import (
        FlextInfraDictToMappingTransformer as FlextInfraDictToMappingTransformer,
    )
    from flext_infra.transformers.helper_consolidation import (
        FlextInfraHelperConsolidationTransformer as FlextInfraHelperConsolidationTransformer,
    )
    from flext_infra.transformers.import_bypass_remover import (
        FlextInfraRefactorImportBypassRemover as FlextInfraRefactorImportBypassRemover,
    )
    from flext_infra.transformers.import_modernizer import (
        FlextInfraRefactorImportModernizer as FlextInfraRefactorImportModernizer,
    )
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer as FlextInfraRefactorLazyImportFixer,
    )
    from flext_infra.transformers.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer as FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer as FlextInfraRefactorMROQualifiedReferenceTransformer,
    )
    from flext_infra.transformers.mro_remover import (
        FlextInfraRefactorMRORemover as FlextInfraRefactorMRORemover,
    )
    from flext_infra.transformers.mro_symbol_propagator import (
        FlextInfraRefactorMROSymbolPropagator as FlextInfraRefactorMROSymbolPropagator,
    )
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer as FlextInfraNestedClassPropagationTransformer,
    )
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities as FlextInfraRefactorTransformerPolicyUtilities,
    )
    from flext_infra.transformers.redundant_cast_remover import (
        FlextInfraRedundantCastRemover as FlextInfraRedundantCastRemover,
    )
    from flext_infra.transformers.signature_propagator import (
        FlextInfraRefactorSignaturePropagator as FlextInfraRefactorSignaturePropagator,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator as FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer as FlextInfraTransformerTier0ImportFixer,
    )
    from flext_infra.transformers.typing_annotation_replacer import (
        FlextInfraTypingAnnotationReplacer as FlextInfraTypingAnnotationReplacer,
    )
    from flext_infra.transformers.typing_unifier import (
        FlextInfraRefactorTypingUnifier as FlextInfraRefactorTypingUnifier,
    )
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor as FlextInfraViolationCensusVisitor,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCensusImportDiscoveryVisitor": [
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusImportDiscoveryVisitor",
    ],
    "FlextInfraCensusUsageCollector": [
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusUsageCollector",
    ],
    "FlextInfraDictToMappingTransformer": [
        "flext_infra.transformers.dict_to_mapping",
        "FlextInfraDictToMappingTransformer",
    ],
    "FlextInfraHelperConsolidationTransformer": [
        "flext_infra.transformers.helper_consolidation",
        "FlextInfraHelperConsolidationTransformer",
    ],
    "FlextInfraNestedClassPropagationTransformer": [
        "flext_infra.transformers.nested_class_propagation",
        "FlextInfraNestedClassPropagationTransformer",
    ],
    "FlextInfraRedundantCastRemover": [
        "flext_infra.transformers.redundant_cast_remover",
        "FlextInfraRedundantCastRemover",
    ],
    "FlextInfraRefactorAliasRemover": [
        "flext_infra.transformers.alias_remover",
        "FlextInfraRefactorAliasRemover",
    ],
    "FlextInfraRefactorClassNestingTransformer": [
        "flext_infra.transformers.class_nesting",
        "FlextInfraRefactorClassNestingTransformer",
    ],
    "FlextInfraRefactorClassReconstructor": [
        "flext_infra.transformers.class_reconstructor",
        "FlextInfraRefactorClassReconstructor",
    ],
    "FlextInfraRefactorDeprecatedRemover": [
        "flext_infra.transformers.deprecated_remover",
        "FlextInfraRefactorDeprecatedRemover",
    ],
    "FlextInfraRefactorImportBypassRemover": [
        "flext_infra.transformers.import_bypass_remover",
        "FlextInfraRefactorImportBypassRemover",
    ],
    "FlextInfraRefactorImportModernizer": [
        "flext_infra.transformers.import_modernizer",
        "FlextInfraRefactorImportModernizer",
    ],
    "FlextInfraRefactorLazyImportFixer": [
        "flext_infra.transformers.lazy_import_fixer",
        "FlextInfraRefactorLazyImportFixer",
    ],
    "FlextInfraRefactorMROPrivateInlineTransformer": [
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROPrivateInlineTransformer",
    ],
    "FlextInfraRefactorMROQualifiedReferenceTransformer": [
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROQualifiedReferenceTransformer",
    ],
    "FlextInfraRefactorMRORemover": [
        "flext_infra.transformers.mro_remover",
        "FlextInfraRefactorMRORemover",
    ],
    "FlextInfraRefactorMROSymbolPropagator": [
        "flext_infra.transformers.mro_symbol_propagator",
        "FlextInfraRefactorMROSymbolPropagator",
    ],
    "FlextInfraRefactorSignaturePropagator": [
        "flext_infra.transformers.signature_propagator",
        "FlextInfraRefactorSignaturePropagator",
    ],
    "FlextInfraRefactorSymbolPropagator": [
        "flext_infra.transformers.symbol_propagator",
        "FlextInfraRefactorSymbolPropagator",
    ],
    "FlextInfraRefactorTransformerPolicyUtilities": [
        "flext_infra.transformers.policy",
        "FlextInfraRefactorTransformerPolicyUtilities",
    ],
    "FlextInfraRefactorTypingUnifier": [
        "flext_infra.transformers.typing_unifier",
        "FlextInfraRefactorTypingUnifier",
    ],
    "FlextInfraTransformerTier0ImportFixer": [
        "flext_infra.transformers.tier0_import_fixer",
        "FlextInfraTransformerTier0ImportFixer",
    ],
    "FlextInfraTypingAnnotationReplacer": [
        "flext_infra.transformers.typing_annotation_replacer",
        "FlextInfraTypingAnnotationReplacer",
    ],
    "FlextInfraViolationCensusVisitor": [
        "flext_infra.transformers.violation_census_visitor",
        "FlextInfraViolationCensusVisitor",
    ],
    "alias_remover": ["flext_infra.transformers.alias_remover", ""],
    "census_visitors": ["flext_infra.transformers.census_visitors", ""],
    "class_nesting": ["flext_infra.transformers.class_nesting", ""],
    "class_reconstructor": ["flext_infra.transformers.class_reconstructor", ""],
    "deprecated_remover": ["flext_infra.transformers.deprecated_remover", ""],
    "dict_to_mapping": ["flext_infra.transformers.dict_to_mapping", ""],
    "helper_consolidation": ["flext_infra.transformers.helper_consolidation", ""],
    "import_bypass_remover": ["flext_infra.transformers.import_bypass_remover", ""],
    "import_modernizer": ["flext_infra.transformers.import_modernizer", ""],
    "lazy_import_fixer": ["flext_infra.transformers.lazy_import_fixer", ""],
    "mro_private_inline": ["flext_infra.transformers.mro_private_inline", ""],
    "mro_remover": ["flext_infra.transformers.mro_remover", ""],
    "mro_symbol_propagator": ["flext_infra.transformers.mro_symbol_propagator", ""],
    "nested_class_propagation": [
        "flext_infra.transformers.nested_class_propagation",
        "",
    ],
    "policy": ["flext_infra.transformers.policy", ""],
    "redundant_cast_remover": ["flext_infra.transformers.redundant_cast_remover", ""],
    "signature_propagator": ["flext_infra.transformers.signature_propagator", ""],
    "symbol_propagator": ["flext_infra.transformers.symbol_propagator", ""],
    "tier0_import_fixer": ["flext_infra.transformers.tier0_import_fixer", ""],
    "typing_annotation_replacer": [
        "flext_infra.transformers.typing_annotation_replacer",
        "",
    ],
    "typing_unifier": ["flext_infra.transformers.typing_unifier", ""],
    "violation_census_visitor": [
        "flext_infra.transformers.violation_census_visitor",
        "",
    ],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraDictToMappingTransformer",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraNestedClassPropagationTransformer",
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
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypingAnnotationReplacer",
    "FlextInfraViolationCensusVisitor",
    "alias_remover",
    "census_visitors",
    "class_nesting",
    "class_reconstructor",
    "deprecated_remover",
    "dict_to_mapping",
    "helper_consolidation",
    "import_bypass_remover",
    "import_modernizer",
    "lazy_import_fixer",
    "mro_private_inline",
    "mro_remover",
    "mro_symbol_propagator",
    "nested_class_propagation",
    "policy",
    "redundant_cast_remover",
    "signature_propagator",
    "symbol_propagator",
    "tier0_import_fixer",
    "typing_annotation_replacer",
    "typing_unifier",
    "violation_census_visitor",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
