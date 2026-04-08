# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Rules package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraClassNestingRefactorRule": (
        "flext_infra.rules.class_nesting",
        "FlextInfraClassNestingRefactorRule",
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
    "FlextInfraRefactorPatternCorrectionsRule": (
        "flext_infra.rules.pattern_corrections",
        "FlextInfraRefactorPatternCorrectionsRule",
    ),
    "class_nesting": "flext_infra.rules.class_nesting",
    "ensure_future_annotations": "flext_infra.rules.ensure_future_annotations",
    "import_modernizer": "flext_infra.rules.import_modernizer",
    "legacy_removal": "flext_infra.rules.legacy_removal",
    "mro_class_migration": "flext_infra.rules.mro_class_migration",
    "pattern_corrections": "flext_infra.rules.pattern_corrections",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
