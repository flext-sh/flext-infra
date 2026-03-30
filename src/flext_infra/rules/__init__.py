# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Rule classes for flext_infra.refactor."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.rules import (
        class_nesting as class_nesting,
        class_reconstructor as class_reconstructor,
        ensure_future_annotations as ensure_future_annotations,
        import_modernizer as import_modernizer,
        legacy_removal as legacy_removal,
        mro_class_migration as mro_class_migration,
        pattern_corrections as pattern_corrections,
    )
    from flext_infra.rules.class_nesting import (
        FlextInfraClassNestingRefactorRule as FlextInfraClassNestingRefactorRule,
    )
    from flext_infra.rules.class_reconstructor import (
        FlextInfraPreCheckGate as FlextInfraPreCheckGate,
        FlextInfraRefactorClassNestingReconstructor as FlextInfraRefactorClassNestingReconstructor,
    )
    from flext_infra.rules.ensure_future_annotations import (
        FlextInfraRefactorEnsureFutureAnnotationsRule as FlextInfraRefactorEnsureFutureAnnotationsRule,
    )
    from flext_infra.rules.import_modernizer import (
        FlextInfraRefactorImportModernizerRule as FlextInfraRefactorImportModernizerRule,
    )
    from flext_infra.rules.legacy_removal import (
        FlextInfraRefactorLegacyRemovalRule as FlextInfraRefactorLegacyRemovalRule,
    )
    from flext_infra.rules.mro_class_migration import (
        FlextInfraRefactorMROClassMigrationRule as FlextInfraRefactorMROClassMigrationRule,
    )
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule as FlextInfraRefactorPatternCorrectionsRule,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraClassNestingRefactorRule": [
        "flext_infra.rules.class_nesting",
        "FlextInfraClassNestingRefactorRule",
    ],
    "FlextInfraPreCheckGate": [
        "flext_infra.rules.class_reconstructor",
        "FlextInfraPreCheckGate",
    ],
    "FlextInfraRefactorClassNestingReconstructor": [
        "flext_infra.rules.class_reconstructor",
        "FlextInfraRefactorClassNestingReconstructor",
    ],
    "FlextInfraRefactorEnsureFutureAnnotationsRule": [
        "flext_infra.rules.ensure_future_annotations",
        "FlextInfraRefactorEnsureFutureAnnotationsRule",
    ],
    "FlextInfraRefactorImportModernizerRule": [
        "flext_infra.rules.import_modernizer",
        "FlextInfraRefactorImportModernizerRule",
    ],
    "FlextInfraRefactorLegacyRemovalRule": [
        "flext_infra.rules.legacy_removal",
        "FlextInfraRefactorLegacyRemovalRule",
    ],
    "FlextInfraRefactorMROClassMigrationRule": [
        "flext_infra.rules.mro_class_migration",
        "FlextInfraRefactorMROClassMigrationRule",
    ],
    "FlextInfraRefactorPatternCorrectionsRule": [
        "flext_infra.rules.pattern_corrections",
        "FlextInfraRefactorPatternCorrectionsRule",
    ],
    "class_nesting": ["flext_infra.rules.class_nesting", ""],
    "class_reconstructor": ["flext_infra.rules.class_reconstructor", ""],
    "ensure_future_annotations": ["flext_infra.rules.ensure_future_annotations", ""],
    "import_modernizer": ["flext_infra.rules.import_modernizer", ""],
    "legacy_removal": ["flext_infra.rules.legacy_removal", ""],
    "mro_class_migration": ["flext_infra.rules.mro_class_migration", ""],
    "pattern_corrections": ["flext_infra.rules.pattern_corrections", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraClassNestingRefactorRule",
    "FlextInfraPreCheckGate",
    "FlextInfraRefactorClassNestingReconstructor",
    "FlextInfraRefactorEnsureFutureAnnotationsRule",
    "FlextInfraRefactorImportModernizerRule",
    "FlextInfraRefactorLegacyRemovalRule",
    "FlextInfraRefactorMROClassMigrationRule",
    "FlextInfraRefactorPatternCorrectionsRule",
    "class_nesting",
    "class_reconstructor",
    "ensure_future_annotations",
    "import_modernizer",
    "legacy_removal",
    "mro_class_migration",
    "pattern_corrections",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
