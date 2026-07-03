# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_TRANSFORMERS_LAZY_IMPORTS_PART_01 = build_lazy_import_map(
    {
        ".bare_except": ("FlextInfraRefactorBareExcept",),
        ".base": ("FlextInfraChangeTrackingTransformer",),
        ".census_visitors": (
            "FlextInfraCensusImportDiscoveryVisitor",
            "FlextInfraCensusUsageCollector",
        ),
        ".class_nesting": ("FlextInfraRefactorClassNestingTransformer",),
        ".class_reconstructor": ("FlextInfraRefactorClassReconstructor",),
        ".cli_modernizer": ("FlextInfraRefactorCliModernizer",),
        ".deprecated_remover": ("FlextInfraRefactorDeprecatedRemover",),
        ".future_import": ("FlextInfraRefactorFutureImport",),
        ".hardcoded_version": ("FlextInfraRefactorHardcodedVersion",),
        ".helper_consolidation": ("FlextInfraHelperConsolidationTransformer",),
        ".import_bypass_remover": ("FlextInfraRefactorImportBypassRemover",),
        ".import_modernizer": ("FlextInfraRefactorImportModernizer",),
        ".lazy_import_fixer": ("FlextInfraRefactorLazyImportFixer",),
        ".logging_modernizer": ("FlextInfraRefactorLoggingModernizer",),
        ".mro_remover": ("FlextInfraRefactorMRORemover",),
        ".mro_symbol_propagator": ("FlextInfraRefactorMROSymbolPropagator",),
        ".nested_class_propagation": ("FlextInfraNestedClassPropagationTransformer",),
        ".open_encoding": ("FlextInfraRefactorOpenEncoding",),
        ".pattern_modernizer": ("FlextInfraRefactorPatternModernizer",),
        ".print_to_logger": ("FlextInfraRefactorPrintToLogger",),
        ".project_alias_migrator": ("FlextInfraRefactorProjectAliasMigrator",),
        ".pydantic_modernizer": ("FlextInfraRefactorPydanticModernizer",),
        ".remove_breakpoint": ("FlextInfraRefactorRemoveBreakpoint",),
        ".result_di_modernizer": ("FlextInfraRefactorResultDiModernizer",),
        ".signature_propagator": ("FlextInfraRefactorSignaturePropagator",),
        ".smells.boolean_logic": ("FlextInfraBooleanLogicFixer",),
        ".symbol_propagator": ("FlextInfraRefactorSymbolPropagator",),
        ".tests_modernizer": ("FlextInfraRefactorTestsModernizer",),
        ".typing_dict_attr": ("FlextInfraRefactorTypingDictAttr",),
        ".typing_dict_import": ("FlextInfraRefactorTypingDictImport",),
        ".typing_unifier": ("FlextInfraRefactorTypingUnifier",),
    },
)

__all__: list[str] = ["FLEXT_INFRA_TRANSFORMERS_LAZY_IMPORTS_PART_01"]
