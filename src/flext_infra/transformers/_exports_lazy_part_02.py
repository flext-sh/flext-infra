# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

FLEXT_INFRA_TRANSFORMERS_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".base": ("FlextInfraRopeTransformer",),
        ".smells": ("smells",),
        ".smells.base": (
            "FlextInfraSmellFixer",
            "auto_fixable_smell_tags",
            "register_smell_fixer",
            "smell_fixer_for",
        ),
        ".tier0_import_fixer": ("FlextInfraTransformerTier0ImportFixer",),
        ".typing_unifier": ("FlextInfraRefactorTypingUnifier",),
        ".violation_census_visitor": ("FlextInfraViolationCensusVisitor",),
    },
)

__all__: list[str] = ["FLEXT_INFRA_TRANSFORMERS_LAZY_IMPORTS_PART_02"]
