# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Rule classes for flext_infra.refactor."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.rules import (
        class_nesting,
        class_reconstructor,
        ensure_future_annotations,
        import_modernizer,
        legacy_removal,
        mro_class_migration,
        pattern_corrections,
    )
    from flext_infra.rules.class_nesting import FlextInfraClassNestingRefactorRule
    from flext_infra.rules.class_reconstructor import (
        FlextInfraPreCheckGate,
        FlextInfraRefactorClassNestingReconstructor,
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
    from flext_infra.rules.pattern_corrections import (
        FlextInfraRefactorPatternCorrectionsRule,
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

__all__ = [
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


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
