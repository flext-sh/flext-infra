# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Rules package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
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
    from flext_infra.rules import (
        class_nesting,
        ensure_future_annotations,
        import_modernizer,
        legacy_removal,
        mro_class_migration,
        pattern_corrections,
    )
    from flext_infra.rules.class_nesting import FlextInfraClassNestingRefactorRule
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
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraClassNestingRefactorRule": "flext_infra.rules.class_nesting",
    "FlextInfraRefactorEnsureFutureAnnotationsRule": "flext_infra.rules.ensure_future_annotations",
    "FlextInfraRefactorImportModernizerRule": "flext_infra.rules.import_modernizer",
    "FlextInfraRefactorLegacyRemovalRule": "flext_infra.rules.legacy_removal",
    "FlextInfraRefactorMROClassMigrationRule": "flext_infra.rules.mro_class_migration",
    "FlextInfraRefactorPatternCorrectionsRule": "flext_infra.rules.pattern_corrections",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
