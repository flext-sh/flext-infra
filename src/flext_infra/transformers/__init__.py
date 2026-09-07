# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.transformers package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import smells as smells
    from .census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
    )
    from .class_reconstructor import FlextInfraRefactorClassReconstructor
    from .compatibility_alias import FlextInfraRefactorCompatibilityAlias
    from .deprecated_remover import FlextInfraRefactorDeprecatedRemover
    from .future_import import FlextInfraRefactorFutureImport
    from .hardcoded_version import FlextInfraRefactorHardcodedVersion
    from .import_bypass_remover import FlextInfraRefactorImportBypassRemover
    from .import_modernizer import FlextInfraRefactorImportModernizer
    from .lazy_import_fixer import FlextInfraRefactorLazyImportFixer
    from .mro_remover import FlextInfraRefactorMroRemover
    from .open_encoding import FlextInfraRefactorOpenEncoding
    from .pattern import FlextInfraRefactorPatternTransformer
    from .pydantic_modernizer import FlextInfraRefactorPydanticModernizer
    from .signature_propagator import FlextInfraRefactorSignaturePropagator
    from .smells.base import (
        FlextInfraSmellFixer,
        auto_fixable_smell_tags,
        register_smell_fixer,
        smell_fixer_for,
    )
    from .smells.boolean_logic import FlextInfraBooleanLogicFixer
    from .symbol_propagator import FlextInfraRefactorSymbolPropagator
    from .tier0_import_fixer import FlextInfraTransformerTier0ImportFixer
    from .typing_unifier import FlextInfraRefactorTypingUnifier
    from .violation_census_visitor import FlextInfraViolationCensusVisitor
__all__: tuple[str, ...] = (
    "FlextInfraBooleanLogicFixer",
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorCompatibilityAlias",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorFutureImport",
    "FlextInfraRefactorHardcodedVersion",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorMroRemover",
    "FlextInfraRefactorOpenEncoding",
    "FlextInfraRefactorPatternTransformer",
    "FlextInfraRefactorPydanticModernizer",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTypingUnifier",
    "FlextInfraSmellFixer",
    "FlextInfraTransformerTier0ImportFixer",
    "FlextInfraViolationCensusVisitor",
    "auto_fixable_smell_tags",
    "register_smell_fixer",
    "smell_fixer_for",
    "smells",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".census_visitors": (
                "FlextInfraCensusImportDiscoveryVisitor",
                "FlextInfraCensusUsageCollector",
            ),
            ".class_reconstructor": ("FlextInfraRefactorClassReconstructor",),
            ".compatibility_alias": ("FlextInfraRefactorCompatibilityAlias",),
            ".deprecated_remover": ("FlextInfraRefactorDeprecatedRemover",),
            ".future_import": ("FlextInfraRefactorFutureImport",),
            ".hardcoded_version": ("FlextInfraRefactorHardcodedVersion",),
            ".import_bypass_remover": ("FlextInfraRefactorImportBypassRemover",),
            ".import_modernizer": ("FlextInfraRefactorImportModernizer",),
            ".lazy_import_fixer": ("FlextInfraRefactorLazyImportFixer",),
            ".mro_remover": ("FlextInfraRefactorMroRemover",),
            ".open_encoding": ("FlextInfraRefactorOpenEncoding",),
            ".pattern": ("FlextInfraRefactorPatternTransformer",),
            ".pydantic_modernizer": ("FlextInfraRefactorPydanticModernizer",),
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
            ".typing_unifier": ("FlextInfraRefactorTypingUnifier",),
            ".violation_census_visitor": ("FlextInfraViolationCensusVisitor",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
