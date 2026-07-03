# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from tests.refactor.test_rope_semantic import (
        TestsFlextInfraRefactorRopeSemantic as TestsFlextInfraRefactorRopeSemantic,
    )
    from tests.refactor.test_rope_stubs import (
        TestsFlextInfraRefactorRopeStubs as TestsFlextInfraRefactorRopeStubs,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_rope_semantic": ("TestsFlextInfraRefactorRopeSemantic",),
        ".test_rope_stubs": ("TestsFlextInfraRefactorRopeStubs",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
