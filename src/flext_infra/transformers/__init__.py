# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Transformer classes for flext_infra.refactor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.transformers.alias_remover import FlextInfraRefactorAliasRemover
    from flext_infra.transformers.census_visitors import (
        CensusImportDiscoveryVisitor,
        CensusUsageCollector,
    )
    from flext_infra.transformers.class_nesting import (
        FlextInfraRefactorClassNestingTransformer,
    )
    from flext_infra.transformers.class_reconstructor import (
        FlextInfraRefactorClassReconstructor,
    )
    from flext_infra.transformers.deprecated_remover import (
        FlextInfraRefactorDeprecatedRemover,
    )
    from flext_infra.transformers.helper_consolidation import (
        HelperConsolidationTransformer,
    )
    from flext_infra.transformers.import_bypass_remover import (
        FlextInfraRefactorImportBypassRemover,
    )
    from flext_infra.transformers.import_insertion import (
        FlextInfraTransformerImportInsertion,
    )
    from flext_infra.transformers.import_modernizer import (
        FlextInfraRefactorImportModernizer,
    )
    from flext_infra.transformers.import_normalizer import (
        ImportNormalizerTransformer,
        ImportNormalizerVisitor,
        ImportViolation,
    )
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer,
    )
    from flext_infra.transformers.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer,
    )
    from flext_infra.transformers.mro_reference_rewriter import (
        FlextInfraRefactorMROReferenceRewriter,
    )
    from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
    from flext_infra.transformers.nested_class_propagation import (
        NestedClassPropagationTransformer,
    )
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities,
    )
    from flext_infra.transformers.project_discovery import ProjectAliasDiscovery
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.typing_annotation_replacer import (
        TypingAnnotationReplacer,
    )
    from flext_infra.transformers.typing_census_visitor import (
        TypingAnnotationCensusVisitor,
    )
    from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
    from flext_infra.transformers.unused_model_remover import UnusedModelRemover
    from flext_infra.transformers.unused_model_visitor import (
        ModelDefinitionCollector,
        ModelReferenceCollector,
    )
    from flext_infra.transformers.violation_census_visitor import ViolationCensusVisitor

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "CensusImportDiscoveryVisitor": ("flext_infra.transformers.census_visitors", "CensusImportDiscoveryVisitor"),
    "CensusUsageCollector": ("flext_infra.transformers.census_visitors", "CensusUsageCollector"),
    "FlextInfraRefactorAliasRemover": ("flext_infra.transformers.alias_remover", "FlextInfraRefactorAliasRemover"),
    "FlextInfraRefactorClassNestingTransformer": ("flext_infra.transformers.class_nesting", "FlextInfraRefactorClassNestingTransformer"),
    "FlextInfraRefactorClassReconstructor": ("flext_infra.transformers.class_reconstructor", "FlextInfraRefactorClassReconstructor"),
    "FlextInfraRefactorDeprecatedRemover": ("flext_infra.transformers.deprecated_remover", "FlextInfraRefactorDeprecatedRemover"),
    "FlextInfraRefactorImportBypassRemover": ("flext_infra.transformers.import_bypass_remover", "FlextInfraRefactorImportBypassRemover"),
    "FlextInfraRefactorImportModernizer": ("flext_infra.transformers.import_modernizer", "FlextInfraRefactorImportModernizer"),
    "FlextInfraRefactorLazyImportFixer": ("flext_infra.transformers.lazy_import_fixer", "FlextInfraRefactorLazyImportFixer"),
    "FlextInfraRefactorMROPrivateInlineTransformer": ("flext_infra.transformers.mro_private_inline", "FlextInfraRefactorMROPrivateInlineTransformer"),
    "FlextInfraRefactorMROQualifiedReferenceTransformer": ("flext_infra.transformers.mro_private_inline", "FlextInfraRefactorMROQualifiedReferenceTransformer"),
    "FlextInfraRefactorMROReferenceRewriter": ("flext_infra.transformers.mro_reference_rewriter", "FlextInfraRefactorMROReferenceRewriter"),
    "FlextInfraRefactorMRORemover": ("flext_infra.transformers.mro_remover", "FlextInfraRefactorMRORemover"),
    "FlextInfraRefactorSymbolPropagator": ("flext_infra.transformers.symbol_propagator", "FlextInfraRefactorSymbolPropagator"),
    "FlextInfraRefactorTransformerPolicyUtilities": ("flext_infra.transformers.policy", "FlextInfraRefactorTransformerPolicyUtilities"),
    "FlextInfraRefactorTypingUnifier": ("flext_infra.transformers.typing_unifier", "FlextInfraRefactorTypingUnifier"),
    "FlextInfraTransformerImportInsertion": ("flext_infra.transformers.import_insertion", "FlextInfraTransformerImportInsertion"),
    "HelperConsolidationTransformer": ("flext_infra.transformers.helper_consolidation", "HelperConsolidationTransformer"),
    "ImportNormalizerTransformer": ("flext_infra.transformers.import_normalizer", "ImportNormalizerTransformer"),
    "ImportNormalizerVisitor": ("flext_infra.transformers.import_normalizer", "ImportNormalizerVisitor"),
    "ImportViolation": ("flext_infra.transformers.import_normalizer", "ImportViolation"),
    "ModelDefinitionCollector": ("flext_infra.transformers.unused_model_visitor", "ModelDefinitionCollector"),
    "ModelReferenceCollector": ("flext_infra.transformers.unused_model_visitor", "ModelReferenceCollector"),
    "NestedClassPropagationTransformer": ("flext_infra.transformers.nested_class_propagation", "NestedClassPropagationTransformer"),
    "ProjectAliasDiscovery": ("flext_infra.transformers.project_discovery", "ProjectAliasDiscovery"),
    "TypingAnnotationCensusVisitor": ("flext_infra.transformers.typing_census_visitor", "TypingAnnotationCensusVisitor"),
    "TypingAnnotationReplacer": ("flext_infra.transformers.typing_annotation_replacer", "TypingAnnotationReplacer"),
    "UnusedModelRemover": ("flext_infra.transformers.unused_model_remover", "UnusedModelRemover"),
    "ViolationCensusVisitor": ("flext_infra.transformers.violation_census_visitor", "ViolationCensusVisitor"),
}

__all__ = [
    "CensusImportDiscoveryVisitor",
    "CensusUsageCollector",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorMROPrivateInlineTransformer",
    "FlextInfraRefactorMROQualifiedReferenceTransformer",
    "FlextInfraRefactorMROReferenceRewriter",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTransformerPolicyUtilities",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraTransformerImportInsertion",
    "HelperConsolidationTransformer",
    "ImportNormalizerTransformer",
    "ImportNormalizerVisitor",
    "ImportViolation",
    "ModelDefinitionCollector",
    "ModelReferenceCollector",
    "NestedClassPropagationTransformer",
    "ProjectAliasDiscovery",
    "TypingAnnotationCensusVisitor",
    "TypingAnnotationReplacer",
    "UnusedModelRemover",
    "ViolationCensusVisitor",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
