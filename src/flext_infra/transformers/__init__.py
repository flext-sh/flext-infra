# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Transformers package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

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
    "FlextInfraViolationCensusVisitor": (
        "flext_infra.transformers.violation_census_visitor",
        "FlextInfraViolationCensusVisitor",
    ),
    "alias_remover": "flext_infra.transformers.alias_remover",
    "census_visitors": "flext_infra.transformers.census_visitors",
    "class_nesting": "flext_infra.transformers.class_nesting",
    "class_reconstructor": "flext_infra.transformers.class_reconstructor",
    "deprecated_remover": "flext_infra.transformers.deprecated_remover",
    "helper_consolidation": "flext_infra.transformers.helper_consolidation",
    "import_bypass_remover": "flext_infra.transformers.import_bypass_remover",
    "import_modernizer": "flext_infra.transformers.import_modernizer",
    "lazy_import_fixer": "flext_infra.transformers.lazy_import_fixer",
    "mro_remover": "flext_infra.transformers.mro_remover",
    "mro_symbol_propagator": "flext_infra.transformers.mro_symbol_propagator",
    "nested_class_propagation": "flext_infra.transformers.nested_class_propagation",
    "policy": "flext_infra.transformers.policy",
    "signature_propagator": "flext_infra.transformers.signature_propagator",
    "symbol_propagator": "flext_infra.transformers.symbol_propagator",
    "tier0_import_fixer": "flext_infra.transformers.tier0_import_fixer",
    "typing_annotation_replacer": "flext_infra.transformers.typing_annotation_replacer",
    "typing_unifier": "flext_infra.transformers.typing_unifier",
    "violation_census_visitor": "flext_infra.transformers.violation_census_visitor",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
