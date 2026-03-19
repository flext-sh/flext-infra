# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Rule classes for flext_infra.refactor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes
    from flext_infra.rules.class_nesting import ClassNestingRefactorRule
    from flext_infra.rules.class_reconstructor import (
        FlextInfraRefactorClassNestingReconstructor,
        FlextInfraRefactorClassReconstructorRule,
        PreCheckGate,
    )
    from flext_infra.rules.ensure_future_annotations import (
        FlextInfraRefactorEnsureFutureAnnotationsRule,
    )
    from flext_infra.rules.import_modernizer import (
        FlextInfraRefactorImportModernizerRule,
    )
    from flext_infra.rules.legacy_removal import FlextInfraRefactorLegacyRemovalRule
    from flext_infra.rules.mro_class_migration import (
        FlextInfraRefactorMROClassMigrationRule,
    )
    from flext_infra.rules.mro_redundancy_checker import (
        FlextInfraRefactorMRORedundancyChecker,
    )
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule,
    )
    from flext_infra.rules.symbol_propagation import (
        FlextInfraRefactorSignaturePropagationRule,
        FlextInfraRefactorSignaturePropagator,
        FlextInfraRefactorSymbolPropagationRule,
    )
    from flext_infra.rules.type_alias_unification import (
        FlextInfraRefactorTypingUnificationRule,
    )
    from flext_infra.rules.typing_census import (
        FlextInfraRefactorTypingAnnotationFixRule,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ClassNestingRefactorRule": (
        "flext_infra.rules.class_nesting",
        "ClassNestingRefactorRule",
    ),
    "FlextInfraRefactorClassNestingReconstructor": (
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassNestingReconstructor",
    ),
    "FlextInfraRefactorClassReconstructorRule": (
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassReconstructorRule",
    ),
    "FlextInfraRefactorEnsureFutureAnnotationsRule": (
        "flext_infra.rules.ensure_future_annotations",
        "FlextInfraRefactorEnsureFutureAnnotationsRule",
    ),
    "FlextInfraRefactorImportModernizerRule": (
        "flext_infra.rules.import_modernizer",
        "FlextInfraRefactorImportModernizerRule",
    ),
    "FlextInfraRefactorLegacyRemovalRule": (
        "flext_infra.rules.legacy_removal",
        "FlextInfraRefactorLegacyRemovalRule",
    ),
    "FlextInfraRefactorMROClassMigrationRule": (
        "flext_infra.rules.mro_class_migration",
        "FlextInfraRefactorMROClassMigrationRule",
    ),
    "FlextInfraRefactorMRORedundancyChecker": (
        "flext_infra.rules.mro_redundancy_checker",
        "FlextInfraRefactorMRORedundancyChecker",
    ),
    "FlextInfraRefactorPatternCorrectionsRule": (
        "flext_infra.rules.pattern_corrections",
        "FlextInfraRefactorPatternCorrectionsRule",
    ),
    "FlextInfraRefactorSignaturePropagationRule": (
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSignaturePropagationRule",
    ),
    "FlextInfraRefactorSignaturePropagator": (
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSignaturePropagator",
    ),
    "FlextInfraRefactorSymbolPropagationRule": (
        "flext_infra.rules.symbol_propagation",
        "FlextInfraRefactorSymbolPropagationRule",
    ),
    "FlextInfraRefactorTypingAnnotationFixRule": (
        "flext_infra.rules.typing_census",
        "FlextInfraRefactorTypingAnnotationFixRule",
    ),
    "FlextInfraRefactorTypingUnificationRule": (
        "flext_infra.rules.type_alias_unification",
        "FlextInfraRefactorTypingUnificationRule",
    ),
    "PreCheckGate": ("flext_infra.rules.class_reconstructor", "PreCheckGate"),
}

__all__ = [
    "ClassNestingRefactorRule",
    "FlextInfraRefactorClassNestingReconstructor",
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorEnsureFutureAnnotationsRule",
    "FlextInfraRefactorImportModernizerRule",
    "FlextInfraRefactorLegacyRemovalRule",
    "FlextInfraRefactorMROClassMigrationRule",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorPatternCorrectionsRule",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSignaturePropagator",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
    "PreCheckGate",
]


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562)."""
    return lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete."""
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
