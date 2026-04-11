# AUTO-GENERATED FILE — Regenerate with: make gen
"""Constants package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from _constants.domain import TestsFlextInfraConstantsDomain
    from _constants.fixtures import TestsFlextInfraConstantsFixtures
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".domain": ("TestsFlextInfraConstantsDomain",),
        ".fixtures": ("TestsFlextInfraConstantsFixtures",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)

__all__ = [
    "TestsFlextInfraConstantsDomain",
    "TestsFlextInfraConstantsFixtures",
]
