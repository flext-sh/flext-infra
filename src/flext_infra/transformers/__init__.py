# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.transformers package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import smells as smells
    from .cast_remover import FlextInfraRefactorCastRemover
    from .census_visitors import (
        FlextInfraCensusImportDiscoveryVisitor,
        FlextInfraCensusUsageCollector,
    )
    from .class_reconstructor import FlextInfraRefactorClassReconstructor
    from .cli_modernizer import FlextInfraRefactorCliModernizer
    from .compatibility_alias import FlextInfraRefactorCompatibilityAlias
    from .deprecated_remover import FlextInfraRefactorDeprecatedRemover
    from .future_import import FlextInfraRefactorFutureImport
    from .hardcoded_version import FlextInfraRefactorHardcodedVersion
    from .import_bypass_remover import FlextInfraRefactorImportBypassRemover
    from .import_modernizer import FlextInfraRefactorImportModernizer
    from .lazy_import_fixer import FlextInfraRefactorLazyImportFixer
    from .logging_modernizer import FlextInfraRefactorLoggingModernizer
    from .open_encoding import FlextInfraRefactorOpenEncoding
    from .pattern import FlextInfraRefactorPatternTransformer
    from .pattern_modernizer import FlextInfraRefactorPatternModernizer
    from .pydantic_modernizer import FlextInfraRefactorPydanticModernizer
    from .result_di_modernizer import FlextInfraRefactorResultDiModernizer
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
    from .typing_dict_attr import FlextInfraRefactorTypingDictAttr
    from .typing_dict_import import FlextInfraRefactorTypingDictImport
    from .typing_unifier import FlextInfraRefactorTypingUnifier
    from .violation_census_visitor import FlextInfraViolationCensusVisitor
__all__: tuple[str, ...] = (
    "FlextInfraBooleanLogicFixer",
    "FlextInfraCensusImportDiscoveryVisitor",
    "FlextInfraCensusUsageCollector",
    "FlextInfraRefactorCastRemover",
    "FlextInfraRefactorClassReconstructor",
    "FlextInfraRefactorCliModernizer",
    "FlextInfraRefactorCompatibilityAlias",
    "FlextInfraRefactorDeprecatedRemover",
    "FlextInfraRefactorFutureImport",
    "FlextInfraRefactorHardcodedVersion",
    "FlextInfraRefactorImportBypassRemover",
    "FlextInfraRefactorImportModernizer",
    "FlextInfraRefactorLazyImportFixer",
    "FlextInfraRefactorLoggingModernizer",
    "FlextInfraRefactorOpenEncoding",
    "FlextInfraRefactorPatternModernizer",
    "FlextInfraRefactorPatternTransformer",
    "FlextInfraRefactorPydanticModernizer",
    "FlextInfraRefactorResultDiModernizer",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagator",
    "FlextInfraRefactorTypingDictAttr",
    "FlextInfraRefactorTypingDictImport",
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
            ".cast_remover": ("FlextInfraRefactorCastRemover",),
            ".census_visitors": (
                "FlextInfraCensusImportDiscoveryVisitor",
                "FlextInfraCensusUsageCollector",
            ),
            ".class_reconstructor": ("FlextInfraRefactorClassReconstructor",),
            ".cli_modernizer": ("FlextInfraRefactorCliModernizer",),
            ".compatibility_alias": ("FlextInfraRefactorCompatibilityAlias",),
            ".deprecated_remover": ("FlextInfraRefactorDeprecatedRemover",),
            ".future_import": ("FlextInfraRefactorFutureImport",),
            ".hardcoded_version": ("FlextInfraRefactorHardcodedVersion",),
            ".import_bypass_remover": ("FlextInfraRefactorImportBypassRemover",),
            ".import_modernizer": ("FlextInfraRefactorImportModernizer",),
            ".lazy_import_fixer": ("FlextInfraRefactorLazyImportFixer",),
            ".logging_modernizer": ("FlextInfraRefactorLoggingModernizer",),
            ".open_encoding": ("FlextInfraRefactorOpenEncoding",),
            ".pattern": ("FlextInfraRefactorPatternTransformer",),
            ".pattern_modernizer": ("FlextInfraRefactorPatternModernizer",),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
