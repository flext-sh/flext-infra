# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.transformers package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.transformers.__unit__ import (
    CHILD_MODULE_PATHS as _CHILD_MODULE_PATHS,
    EXCLUDED_LAZY_NAMES as _EXCLUDED_LAZY_NAMES,
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.transformers import smells as smells
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

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = merge_lazy_imports(
    _CHILD_MODULE_PATHS,
    build_lazy_import_map(
        _LAZY_MODULES,
        alias_groups=_LAZY_ALIAS_GROUPS,
        sort_keys=False,
    ),
    exclude_names=_EXCLUDED_LAZY_NAMES,
    module_name=__name__,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
