# AUTO-GENERATED FILE — Regenerate with: make gen
"""Phases package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps.phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps.phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps.phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps.phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
    from flext_infra.deps.phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps.phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
    from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".consolidate_groups": ("FlextInfraConsolidateGroupsPhase",),
        ".ensure_coverage": ("FlextInfraEnsureCoverageConfigPhase",),
        ".ensure_formatting": ("FlextInfraEnsureFormattingToolingPhase",),
        ".ensure_mypy": ("FlextInfraEnsureMypyConfigPhase",),
        ".ensure_namespace": ("FlextInfraEnsureNamespaceToolingPhase",),
        ".ensure_pydantic_mypy": ("FlextInfraEnsurePydanticMypyConfigPhase",),
        ".ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
        ".ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
        ".ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
        ".ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
        ".inject_comments": ("FlextInfraInjectCommentsPhase",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
