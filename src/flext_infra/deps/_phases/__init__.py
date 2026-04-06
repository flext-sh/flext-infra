# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Phases package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.deps._phases.consolidate_groups as _flext_infra_deps__phases_consolidate_groups

    consolidate_groups = _flext_infra_deps__phases_consolidate_groups
    import flext_infra.deps._phases.ensure_coverage as _flext_infra_deps__phases_ensure_coverage
    from flext_infra.deps._phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase,
    )

    ensure_coverage = _flext_infra_deps__phases_ensure_coverage
    import flext_infra.deps._phases.ensure_extra_paths as _flext_infra_deps__phases_ensure_extra_paths
    from flext_infra.deps._phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase,
    )

    ensure_extra_paths = _flext_infra_deps__phases_ensure_extra_paths
    import flext_infra.deps._phases.ensure_formatting as _flext_infra_deps__phases_ensure_formatting
    from flext_infra.deps._phases.ensure_extra_paths import (
        FlextInfraEnsureExtraPathsPhase,
    )

    ensure_formatting = _flext_infra_deps__phases_ensure_formatting
    import flext_infra.deps._phases.ensure_mypy as _flext_infra_deps__phases_ensure_mypy
    from flext_infra.deps._phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase,
    )

    ensure_mypy = _flext_infra_deps__phases_ensure_mypy
    import flext_infra.deps._phases.ensure_namespace as _flext_infra_deps__phases_ensure_namespace
    from flext_infra.deps._phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase

    ensure_namespace = _flext_infra_deps__phases_ensure_namespace
    import flext_infra.deps._phases.ensure_pydantic_mypy as _flext_infra_deps__phases_ensure_pydantic_mypy
    from flext_infra.deps._phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase,
    )

    ensure_pydantic_mypy = _flext_infra_deps__phases_ensure_pydantic_mypy
    import flext_infra.deps._phases.ensure_pyrefly as _flext_infra_deps__phases_ensure_pyrefly
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase,
    )

    ensure_pyrefly = _flext_infra_deps__phases_ensure_pyrefly
    import flext_infra.deps._phases.ensure_pyright as _flext_infra_deps__phases_ensure_pyright
    from flext_infra.deps._phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase,
    )

    ensure_pyright = _flext_infra_deps__phases_ensure_pyright
    import flext_infra.deps._phases.ensure_pyright_envs as _flext_infra_deps__phases_ensure_pyright_envs
    from flext_infra.deps._phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase,
    )

    ensure_pyright_envs = _flext_infra_deps__phases_ensure_pyright_envs
    import flext_infra.deps._phases.ensure_pytest as _flext_infra_deps__phases_ensure_pytest
    from flext_infra.deps._phases.ensure_pyright_envs import FlextInfraEnsurePyrightEnvs

    ensure_pytest = _flext_infra_deps__phases_ensure_pytest
    import flext_infra.deps._phases.ensure_ruff as _flext_infra_deps__phases_ensure_ruff
    from flext_infra.deps._phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase

    ensure_ruff = _flext_infra_deps__phases_ensure_ruff
    import flext_infra.deps._phases.inject_comments as _flext_infra_deps__phases_inject_comments
    from flext_infra.deps._phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase

    inject_comments = _flext_infra_deps__phases_inject_comments
    from flext_infra.deps._phases.inject_comments import FlextInfraInjectCommentsPhase
_LAZY_IMPORTS = {
    "FlextInfraConsolidateGroupsPhase": (
        "flext_infra.deps._phases.consolidate_groups",
        "FlextInfraConsolidateGroupsPhase",
    ),
    "FlextInfraEnsureCoverageConfigPhase": (
        "flext_infra.deps._phases.ensure_coverage",
        "FlextInfraEnsureCoverageConfigPhase",
    ),
    "FlextInfraEnsureExtraPathsPhase": (
        "flext_infra.deps._phases.ensure_extra_paths",
        "FlextInfraEnsureExtraPathsPhase",
    ),
    "FlextInfraEnsureFormattingToolingPhase": (
        "flext_infra.deps._phases.ensure_formatting",
        "FlextInfraEnsureFormattingToolingPhase",
    ),
    "FlextInfraEnsureMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_mypy",
        "FlextInfraEnsureMypyConfigPhase",
    ),
    "FlextInfraEnsureNamespaceToolingPhase": (
        "flext_infra.deps._phases.ensure_namespace",
        "FlextInfraEnsureNamespaceToolingPhase",
    ),
    "FlextInfraEnsurePydanticMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "FlextInfraEnsurePydanticMypyConfigPhase",
    ),
    "FlextInfraEnsurePyreflyConfigPhase": (
        "flext_infra.deps._phases.ensure_pyrefly",
        "FlextInfraEnsurePyreflyConfigPhase",
    ),
    "FlextInfraEnsurePyrightConfigPhase": (
        "flext_infra.deps._phases.ensure_pyright",
        "FlextInfraEnsurePyrightConfigPhase",
    ),
    "FlextInfraEnsurePyrightEnvs": (
        "flext_infra.deps._phases.ensure_pyright_envs",
        "FlextInfraEnsurePyrightEnvs",
    ),
    "FlextInfraEnsurePytestConfigPhase": (
        "flext_infra.deps._phases.ensure_pytest",
        "FlextInfraEnsurePytestConfigPhase",
    ),
    "FlextInfraEnsureRuffConfigPhase": (
        "flext_infra.deps._phases.ensure_ruff",
        "FlextInfraEnsureRuffConfigPhase",
    ),
    "FlextInfraInjectCommentsPhase": (
        "flext_infra.deps._phases.inject_comments",
        "FlextInfraInjectCommentsPhase",
    ),
    "consolidate_groups": "flext_infra.deps._phases.consolidate_groups",
    "ensure_coverage": "flext_infra.deps._phases.ensure_coverage",
    "ensure_extra_paths": "flext_infra.deps._phases.ensure_extra_paths",
    "ensure_formatting": "flext_infra.deps._phases.ensure_formatting",
    "ensure_mypy": "flext_infra.deps._phases.ensure_mypy",
    "ensure_namespace": "flext_infra.deps._phases.ensure_namespace",
    "ensure_pydantic_mypy": "flext_infra.deps._phases.ensure_pydantic_mypy",
    "ensure_pyrefly": "flext_infra.deps._phases.ensure_pyrefly",
    "ensure_pyright": "flext_infra.deps._phases.ensure_pyright",
    "ensure_pyright_envs": "flext_infra.deps._phases.ensure_pyright_envs",
    "ensure_pytest": "flext_infra.deps._phases.ensure_pytest",
    "ensure_ruff": "flext_infra.deps._phases.ensure_ruff",
    "inject_comments": "flext_infra.deps._phases.inject_comments",
}

__all__ = [
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureExtraPathsPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePyrightEnvs",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraInjectCommentsPhase",
    "consolidate_groups",
    "ensure_coverage",
    "ensure_extra_paths",
    "ensure_formatting",
    "ensure_mypy",
    "ensure_namespace",
    "ensure_pydantic_mypy",
    "ensure_pyrefly",
    "ensure_pyright",
    "ensure_pyright_envs",
    "ensure_pytest",
    "ensure_ruff",
    "inject_comments",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
