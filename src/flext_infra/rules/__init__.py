# AUTO-GENERATED FILE — Regenerate with: make gen
"""Rules package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".class_nesting": ("FlextInfraClassNestingRefactorRule",),
        ".ensure_future_annotations": (
            "FlextInfraRefactorEnsureFutureAnnotationsRule",
        ),
        ".import_modernizer": ("FlextInfraRefactorImportModernizerRule",),
        ".legacy_removal": ("FlextInfraRefactorLegacyRemovalRule",),
        ".mro_class_migration": ("FlextInfraRefactorMROClassMigrationRule",),
        ".pattern_corrections": ("FlextInfraRefactorPatternCorrectionsRule",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
