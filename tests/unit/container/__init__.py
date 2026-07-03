# AUTO-GENERATED FILE — Regenerate with: make gen
"""Container package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.container.test_infra_container import (
        TestsFlextInfraContainerInfraContainer as TestsFlextInfraContainerInfraContainer,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_container": ("TestsFlextInfraContainerInfraContainer",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
