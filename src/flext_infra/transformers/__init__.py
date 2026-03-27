# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Transformer classes for flext_infra.refactor."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.transformers.alias_remover import FlextInfraRefactorAliasRemover
    from flext_infra.transformers.census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
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
        FlextInfraHelperConsolidationTransformer,
    )
    from flext_infra.transformers.import_bypass_remover import (
        FlextInfraRefactorImportBypassRemover,
    )
    from flext_infra.transformers.import_modernizer import (
        FlextInfraRefactorImportModernizer,
    )
    from flext_infra.transformers.lazy_import_fixer import (
        FlextInfraRefactorLazyImportFixer,
    )
    from flext_infra.transformers.mro_private_inline import (
        FlextInfraRefactorMROPrivateInlineTransformer,
        FlextInfraRefactorMROQualifiedReferenceTransformer,
    )
    from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
    from flext_infra.transformers.mro_symbol_propagator import (
        FlextInfraRefactorMROSymbolPropagator,
    )
    from flext_infra.transformers.nested_class_propagation import (
        FlextInfraNestedClassPropagationTransformer,
    )
    from flext_infra.transformers.policy import (
        FlextInfraRefactorTransformerPolicyUtilities,
    )
    from flext_infra.transformers.symbol_propagator import (
        FlextInfraRefactorSymbolPropagator,
    )
    from flext_infra.transformers.tier0_import_fixer import (
        FlextInfraTransformerTier0ImportFixer,
    )
    from flext_infra.transformers.typing_annotation_replacer import (
        FlextInfraTypingAnnotationReplacer,
    )
    from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
    from flext_infra.transformers.violation_census_visitor import (
        FlextInfraViolationCensusVisitor,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraCensusImportDiscoveryVisitor": [
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusImportDiscoveryVisitor",
    ],
    "FlextInfraCensusUsageCollector": [
        "flext_infra.transformers.census_visitors",
        "FlextInfraCensusUsageCollector",
    ],
    "FlextInfraHelperConsolidationTransformer": [
        "flext_infra.transformers.helper_consolidation",
        "FlextInfraHelperConsolidationTransformer",
    ],
    "FlextInfraNestedClassPropagationTransformer": [
        "flext_infra.transformers.nested_class_propagation",
        "FlextInfraNestedClassPropagationTransformer",
    ],
    "FlextInfraRefactorAliasRemover": [
        "flext_infra.transformers.alias_remover",
        "FlextInfraRefactorAliasRemover",
    ],
    "FlextInfraRefactorClassNestingTransformer": [
        "flext_infra.transformers.class_nesting",
        "FlextInfraRefactorClassNestingTransformer",
    ],
    "FlextInfraRefactorClassReconstructor": [
        "flext_infra.transformers.class_reconstructor",
        "FlextInfraRefactorClassReconstructor",
    ],
    "FlextInfraRefactorDeprecatedRemover": [
        "flext_infra.transformers.deprecated_remover",
        "FlextInfraRefactorDeprecatedRemover",
    ],
    "FlextInfraRefactorImportBypassRemover": [
        "flext_infra.transformers.import_bypass_remover",
        "FlextInfraRefactorImportBypassRemover",
    ],
    "FlextInfraRefactorImportModernizer": [
        "flext_infra.transformers.import_modernizer",
        "FlextInfraRefactorImportModernizer",
    ],
    "FlextInfraRefactorLazyImportFixer": [
        "flext_infra.transformers.lazy_import_fixer",
        "FlextInfraRefactorLazyImportFixer",
    ],
    "FlextInfraRefactorMROPrivateInlineTransformer": [
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROPrivateInlineTransformer",
    ],
    "FlextInfraRefactorMROQualifiedReferenceTransformer": [
        "flext_infra.transformers.mro_private_inline",
        "FlextInfraRefactorMROQualifiedReferenceTransformer",
    ],
    "FlextInfraRefactorMRORemover": [
        "flext_infra.transformers.mro_remover",
        "FlextInfraRefactorMRORemover",
    ],
    "FlextInfraRefactorMROSymbolPropagator": [
        "flext_infra.transformers.mro_symbol_propagator",
        "FlextInfraRefactorMROSymbolPropagator",
    ],
    "FlextInfraRefactorSymbolPropagator": [
        "flext_infra.transformers.symbol_propagator",
        "FlextInfraRefactorSymbolPropagator",
    ],
    "FlextInfraRefactorTransformerPolicyUtilities": [
        "flext_infra.transformers.policy",
        "FlextInfraRefactorTransformerPolicyUtilities",
    ],
    "FlextInfraRefactorTypingUnifier": [
        "flext_infra.transformers.typing_unifier",
        "FlextInfraRefactorTypingUnifier",
    ],
    "FlextInfraTransformerTier0ImportFixer": [
        "flext_infra.transformers.tier0_import_fixer",
        "FlextInfraTransformerTier0ImportFixer",
    ],
    "FlextInfraTypingAnnotationReplacer": [
        "flext_infra.transformers.typing_annotation_replacer",
        "FlextInfraTypingAnnotationReplacer",
    ],
    "FlextInfraViolationCensusVisitor": [
        "flext_infra.transformers.violation_census_visitor",
        "FlextInfraViolationCensusVisitor",
    ],
}

__all__ = [
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraHelperConsolidationTransformer",
    "FlextInfraNestedClassPropagationTransformer",
    "FlextInfraRefactorAliasRemover",
    "FlextInfraRefactorClassNestingTransformer",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorMROPrivateInlineTransformer",
    "FlextInfraRefactorMROQualifiedReferenceTransformer",
    "FlextInfraRefactorMRORemover",
    "FlextInfraRefactorMROSymbolPropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTransformerPolicyUtilities",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraTypingAnnotationReplacer",
    "FlextInfraViolationCensusVisitor",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
