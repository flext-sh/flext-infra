# AUTO-GENERATED FILE — Regenerate with: make gen
"""Transformers package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": (
            "FlextInfraChangeTrackingTransformer",
            "FlextInfraRopeTransformer",
        ),
        ".census_visitors": (
            "FlextInfraCensusImportDiscoveryVisitor",
            "FlextInfraCensusUsageCollector",
        ),
        ".class_nesting": ("FlextInfraRefactorClassNestingTransformer",),
        ".class_reconstructor": ("FlextInfraRefactorClassReconstructor",),
        ".cli_modernizer": ("FlextInfraRefactorCliModernizer",),
        ".deprecated_remover": ("FlextInfraRefactorDeprecatedRemover",),
        ".helper_consolidation": ("FlextInfraHelperConsolidationTransformer",),
        ".import_bypass_remover": ("FlextInfraRefactorImportBypassRemover",),
        ".import_modernizer": ("FlextInfraRefactorImportModernizer",),
        ".lazy_import_fixer": ("FlextInfraRefactorLazyImportFixer",),
        ".logging_modernizer": ("FlextInfraRefactorLoggingModernizer",),
        ".mro_remover": ("FlextInfraRefactorMRORemover",),
        ".mro_symbol_propagator": ("FlextInfraRefactorMROSymbolPropagator",),
        ".nested_class_propagation": ("FlextInfraNestedClassPropagationTransformer",),
        ".pattern_modernizer": ("FlextInfraRefactorPatternModernizer",),
        ".pydantic_modernizer": ("FlextInfraRefactorPydanticModernizer",),
        ".result_di_modernizer": ("FlextInfraRefactorResultDiModernizer",),
        ".signature_propagator": ("FlextInfraRefactorSignaturePropagator",),
        ".symbol_propagator": ("FlextInfraRefactorSymbolPropagator",),
        ".tests_modernizer": ("FlextInfraRefactorTestsModernizer",),
        ".tier0_import_fixer": ("FlextInfraTransformerTier0ImportFixer",),
        ".typing_unifier": ("FlextInfraRefactorTypingUnifier",),
        ".violation_census_visitor": ("FlextInfraViolationCensusVisitor",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
