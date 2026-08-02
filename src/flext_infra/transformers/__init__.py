# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.transformers package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextInfraChangeTrackingTransformer", "FlextInfraRopeTransformer"),
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
    ".tier0_import_fixer": ("FlextInfraTransformerTier0ImportFixer",),
    ".typing_dict_attr": ("FlextInfraRefactorTypingDictAttr",),
    ".typing_dict_import": ("FlextInfraRefactorTypingDictImport",),
    ".typing_unifier": ("FlextInfraRefactorTypingUnifier",),
    ".violation_census_visitor": ("FlextInfraViolationCensusVisitor",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
