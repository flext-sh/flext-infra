# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Rules package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.rules.class_nesting as _flext_infra_rules_class_nesting

    class_nesting = _flext_infra_rules_class_nesting
    import flext_infra.rules.ensure_future_annotations as _flext_infra_rules_ensure_future_annotations
    from flext_infra.rules.class_nesting import FlextInfraClassNestingRefactorRule

    ensure_future_annotations = _flext_infra_rules_ensure_future_annotations
    import flext_infra.rules.import_modernizer as _flext_infra_rules_import_modernizer
    from flext_infra.rules.ensure_future_annotations import (
        FlextInfraRefactorEnsureFutureAnnotationsRule,
    )

    import_modernizer = _flext_infra_rules_import_modernizer
    import flext_infra.rules.legacy_removal as _flext_infra_rules_legacy_removal
    from flext_infra.rules.import_modernizer import (
        FlextInfraRefactorImportModernizerRule,
    )

    legacy_removal = _flext_infra_rules_legacy_removal
    import flext_infra.rules.mro_class_migration as _flext_infra_rules_mro_class_migration
    from flext_infra.rules.legacy_removal import FlextInfraRefactorLegacyRemovalRule

    mro_class_migration = _flext_infra_rules_mro_class_migration
    import flext_infra.rules.pattern_corrections as _flext_infra_rules_pattern_corrections
    from flext_infra.rules.mro_class_migration import (
        FlextInfraRefactorMROClassMigrationRule,
    )

    pattern_corrections = _flext_infra_rules_pattern_corrections
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule,
    )
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
    "c": ("flext_core.constants", "FlextConstants"),
    "class_nesting": "flext_infra.rules.class_nesting",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "ensure_future_annotations": "flext_infra.rules.ensure_future_annotations",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "import_modernizer": "flext_infra.rules.import_modernizer",
    "legacy_removal": "flext_infra.rules.legacy_removal",
    "m": ("flext_core.models", "FlextModels"),
    "mro_class_migration": "flext_infra.rules.mro_class_migration",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pattern_corrections": "flext_infra.rules.pattern_corrections",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraClassNestingRefactorRule",
    "FlextInfraRefactorEnsureFutureAnnotationsRule",
    "FlextInfraRefactorImportModernizerRule",
    "FlextInfraRefactorLegacyRemovalRule",
    "FlextInfraRefactorMROClassMigrationRule",
    "FlextInfraRefactorPatternCorrectionsRule",
    "c",
    "class_nesting",
    "d",
    "e",
    "ensure_future_annotations",
    "h",
    "import_modernizer",
    "legacy_removal",
    "m",
    "mro_class_migration",
    "p",
    "pattern_corrections",
    "r",
    "s",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
