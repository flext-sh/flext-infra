# AUTO-GENERATED FILE — Regenerate with: make gen
"""Transformers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if TYPE_CHECKING:
    from flext_infra.transformers.base import (
        FlextInfraChangeTrackingTransformer as FlextInfraChangeTrackingTransformer,
        FlextInfraRopeTransformer as FlextInfraRopeTransformer,
    )
    from flext_infra.transformers.cast_remover import (
        FlextInfraRefactorCastRemover as FlextInfraRefactorCastRemover,
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
    from flext_infra.transformers.cli_modernizer import (
        FlextInfraRefactorCliModernizer as FlextInfraRefactorCliModernizer,
    )
    from flext_infra.transformers.compatibility_alias import (
        FlextInfraRefactorCompatibilityAlias as FlextInfraRefactorCompatibilityAlias,
    )
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover as FlextInfraRefactorDeprecatedRemover,
    )
    from flext_infra.transformers.future_import import (
        FlextInfraRefactorFutureImport as FlextInfraRefactorFutureImport,
    )
    from flext_infra.transformers.hardcoded_version import (
        FlextInfraRefactorHardcodedVersion as FlextInfraRefactorHardcodedVersion,
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
    from flext_infra.transformers.logging_modernizer import (
        FlextInfraRefactorLoggingModernizer as FlextInfraRefactorLoggingModernizer,
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
    from flext_infra.transformers.open_encoding import (
        FlextInfraRefactorOpenEncoding as FlextInfraRefactorOpenEncoding,
    )
    from flext_infra.transformers.pattern import (
        FlextInfraRefactorPatternTransformer as FlextInfraRefactorPatternTransformer,
    )
    from flext_infra.transformers.pattern_modernizer import (
        FlextInfraRefactorPatternModernizer as FlextInfraRefactorPatternModernizer,
    )
    from flext_infra.transformers.project_alias_migrator import (
        FlextInfraRefactorProjectAliasMigrator as FlextInfraRefactorProjectAliasMigrator,
    )
    from flext_infra.transformers.pydantic_modernizer import (
        FlextInfraRefactorPydanticModernizer as FlextInfraRefactorPydanticModernizer,
    )
    from flext_infra.transformers.result_di_modernizer import (
        FlextInfraRefactorResultDiModernizer as FlextInfraRefactorResultDiModernizer,
    )
    from flext_infra.transformers.signature_propagator import (
        FlextInfraRefactorSignaturePropagator as FlextInfraRefactorSignaturePropagator,
    )
    from flext_infra.transformers.smells.base import (
        FlextInfraSmellFixer as FlextInfraSmellFixer,
        auto_fixable_smell_tags as auto_fixable_smell_tags,
        register_smell_fixer as register_smell_fixer,
        smell_fixer_for as smell_fixer_for,
    )
    from flext_infra.transformers.smells.boolean_logic import (
        FlextInfraBooleanLogicFixer as FlextInfraBooleanLogicFixer,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator as FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.tests_modernizer import (
        FlextInfraRefactorTestsModernizer as FlextInfraRefactorTestsModernizer,
    )
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer as FlextInfraTransformerTier0ImportFixer,
    )
    from flext_infra.transformers.typing_dict_attr import (
        FlextInfraRefactorTypingDictAttr as FlextInfraRefactorTypingDictAttr,
    )
    from flext_infra.transformers.typing_dict_import import (
        FlextInfraRefactorTypingDictImport as FlextInfraRefactorTypingDictImport,
    )
    from flext_infra.transformers.typing_unifier import (
        FlextInfraRefactorTypingUnifier as FlextInfraRefactorTypingUnifier,
    )
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor as FlextInfraViolationCensusVisitor,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    (".smells",),
    build_lazy_import_map(
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
            ".nested_class_propagation": (
                "FlextInfraNestedClassPropagationTransformer",
            ),
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
    ),
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
    module_name=__name__,
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
