# AUTO-GENERATED FILE — Regenerate with: make gen
"""Phases package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra.deps.phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps.phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps.phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps.phases.ensure_mypy import (
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps.phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pytest import (
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps.phases.ensure_ruff import (
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps.phases.inject_comments import (
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
