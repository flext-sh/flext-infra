# AUTO-GENERATED FILE — Regenerate with: make gen
"""Rules package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraClassNestingRefactorRule": ".class_nesting",
    "FlextInfraRefactorEnsureFutureAnnotationsRule": ".ensure_future_annotations",
    "FlextInfraRefactorImportModernizerRule": ".import_modernizer",
    "FlextInfraRefactorLegacyRemovalRule": ".legacy_removal",
    "FlextInfraRefactorMROClassMigrationRule": ".mro_class_migration",
    "FlextInfraRefactorPatternCorrectionsRule": ".pattern_corrections",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
