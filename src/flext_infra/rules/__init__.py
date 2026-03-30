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
        class_nesting,
        class_reconstructor,
        ensure_future_annotations,
        import_modernizer,
        legacy_removal,
        mro_class_migration,
        pattern_corrections,
    )
    from flext_infra.rules.class_nesting import *
    from flext_infra.rules.class_reconstructor import *
    from flext_infra.rules.ensure_future_annotations import *
    from flext_infra.rules.import_modernizer import *
    from flext_infra.rules.legacy_removal import *
    from flext_infra.rules.mro_class_migration import *
    from flext_infra.rules.pattern_corrections import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraClassNestingRefactorRule": "flext_infra.rules.class_nesting",
    "FlextInfraPreCheckGate": "flext_infra.rules.class_reconstructor",
    "FlextInfraRefactorClassNestingReconstructor": "flext_infra.rules.class_reconstructor",
    "FlextInfraRefactorEnsureFutureAnnotationsRule": "flext_infra.rules.ensure_future_annotations",
    "FlextInfraRefactorImportModernizerRule": "flext_infra.rules.import_modernizer",
    "FlextInfraRefactorLegacyRemovalRule": "flext_infra.rules.legacy_removal",
    "FlextInfraRefactorMROClassMigrationRule": "flext_infra.rules.mro_class_migration",
    "FlextInfraRefactorPatternCorrectionsRule": "flext_infra.rules.pattern_corrections",
    "class_nesting": "flext_infra.rules.class_nesting",
    "class_reconstructor": "flext_infra.rules.class_reconstructor",
    "ensure_future_annotations": "flext_infra.rules.ensure_future_annotations",
    "import_modernizer": "flext_infra.rules.import_modernizer",
    "legacy_removal": "flext_infra.rules.legacy_removal",
    "mro_class_migration": "flext_infra.rules.mro_class_migration",
    "pattern_corrections": "flext_infra.rules.pattern_corrections",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
