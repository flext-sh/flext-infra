# AUTO-GENERATED FILE — Regenerate with: make gen
from flext_infra.transformers import smells as smells
from flext_infra.transformers.bare_except import (
    FlextInfraRefactorBareExcept as FlextInfraRefactorBareExcept,
)
from flext_infra.transformers.base import (
    FlextInfraChangeTrackingTransformer as FlextInfraChangeTrackingTransformer,
    FlextInfraRopeTransformer as FlextInfraRopeTransformer,
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
from flext_infra.transformers.pattern_modernizer import (
    FlextInfraRefactorPatternModernizer as FlextInfraRefactorPatternModernizer,
)
from flext_infra.transformers.print_to_logger import (
    FlextInfraRefactorPrintToLogger as FlextInfraRefactorPrintToLogger,
)
from flext_infra.transformers.project_alias_migrator import (
    FlextInfraRefactorProjectAliasMigrator as FlextInfraRefactorProjectAliasMigrator,
)
from flext_infra.transformers.pydantic_modernizer import (
    FlextInfraRefactorPydanticModernizer as FlextInfraRefactorPydanticModernizer,
)
from flext_infra.transformers.remove_breakpoint import (
    FlextInfraRefactorRemoveBreakpoint as FlextInfraRefactorRemoveBreakpoint,
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

__all__ = (
    "FlextInfraBooleanLogicFixer",
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraChangeTrackingTransformer",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraRefactorBareExcept",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorCliModernizer",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorFutureImport",
    "FlextInfraRefactorHardcodedVersion",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorLoggingModernizer",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorOpenEncoding",
    "FlextInfraRefactorPatternModernizer",
    "FlextInfraRefactorPrintToLogger",
    "FlextInfraRefactorProjectAliasMigrator",
    "FlextInfraRefactorPydanticModernizer",
    "FlextInfraRefactorRemoveBreakpoint",
    "FlextInfraRefactorResultDiModernizer",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTestsModernizer",
    "FlextInfraRefactorTypingDictAttr",
    "FlextInfraRefactorTypingDictImport",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraRopeTransformer",
    "FlextInfraSmellFixer",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraViolationCensusVisitor",
    "auto_fixable_smell_tags",
    "register_smell_fixer",
    "smell_fixer_for",
    "smells",
)
