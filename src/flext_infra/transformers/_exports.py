# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export registry."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, merge_lazy_imports

_LOCAL_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": (
            "FlextInfraChangeTrackingTransformer",
            "FlextInfraRopeTransformer",
        ),
        ".cast_remover": ("FlextInfraRefactorCastRemover",),
        ".census_visitors": (
            "FlextInfraCensusImportDiscoveryVisitor",
            "FlextInfraCensusUsageCollector",
        ),
        ".class_nesting": ("FlextInfraRefactorClassNestingTransformer",),
        ".class_reconstructor": ("FlextInfraRefactorClassReconstructor",),
        ".cli_modernizer": ("FlextInfraRefactorCliModernizer",),
        ".compatibility_alias": ("FlextInfraRefactorCompatibilityAlias",),
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
        ".pattern": ("FlextInfraRefactorPatternTransformer",),
        ".pattern_modernizer": ("FlextInfraRefactorPatternModernizer",),
        ".project_alias_migrator": ("FlextInfraRefactorProjectAliasMigrator",),
        ".pydantic_modernizer": ("FlextInfraRefactorPydanticModernizer",),
        ".result_di_modernizer": ("FlextInfraRefactorResultDiModernizer",),
        ".signature_propagator": ("FlextInfraRefactorSignaturePropagator",),
        ".smells": ("smells",),
        ".smells.base": (
            "FlextInfraSmellFixer",
            "auto_fixable_smell_tags",
            "register_smell_fixer",
            "smell_fixer_for",
        ),
        ".smells.boolean_logic": ("FlextInfraBooleanLogicFixer",),
        ".symbol_propagator": ("FlextInfraRefactorSymbolPropagator",),
        ".tests_modernizer": ("FlextInfraRefactorTestsModernizer",),
        ".tier0_import_fixer": ("FlextInfraTransformerTier0ImportFixer",),
        ".typing_dict_attr": ("FlextInfraRefactorTypingDictAttr",),
        ".typing_dict_import": ("FlextInfraRefactorTypingDictImport",),
        ".typing_unifier": ("FlextInfraRefactorTypingUnifier",),
        ".violation_census_visitor": ("FlextInfraViolationCensusVisitor",),
    },
)

FLEXT_INFRA_TRANSFORMERS_LAZY_IMPORTS = merge_lazy_imports(
    (".smells",),
    _LOCAL_LAZY_IMPORTS,
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name="flext_infra.transformers",
)

__all__: list[str] = ["FLEXT_INFRA_TRANSFORMERS_LAZY_IMPORTS"]
