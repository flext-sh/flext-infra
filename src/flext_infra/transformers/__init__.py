# AUTO-GENERATED FILE — Regenerate with: make gen
from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraCensusImportDiscoveryVisitor": ".census_visitors",
    "FlextInfraCensusUsageCollector": ".census_visitors",
    "FlextInfraChangeTrackingTransformer": "._base",
    "FlextInfraHelperConsolidationTransformer": ".helper_consolidation",
    "FlextInfraNestedClassPropagationTransformer": ".nested_class_propagation",
    "FlextInfraRefactorAliasRemover": ".alias_remover",
    "FlextInfraRefactorClassNestingTransformer": ".class_nesting",
    "FlextInfraRefactorClassReconstructor": ".class_reconstructor",
    "FlextInfraRefactorDeprecatedRemover": ".deprecated_remover",
    "FlextInfraRefactorImportBypassRemover": ".import_bypass_remover",
    "FlextInfraRefactorImportModernizer": ".import_modernizer",
    "FlextInfraRefactorLazyImportFixer": ".lazy_import_fixer",
    "FlextInfraRefactorMRORemover": ".mro_remover",
    "FlextInfraRefactorMROSymbolPropagator": ".mro_symbol_propagator",
    "FlextInfraRefactorSignaturePropagator": ".signature_propagator",
    "FlextInfraRefactorSymbolPropagator": ".symbol_propagator",
    "FlextInfraRefactorTypingUnifier": ".typing_unifier",
    "FlextInfraRopeTransformer": "._base",
    "FlextInfraTransformerTier0ImportFixer": ".tier0_import_fixer",
    "FlextInfraTypingAnnotationReplacer": ".typing_annotation_replacer",
    "FlextInfraViolationCensusVisitor": ".violation_census_visitor",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
