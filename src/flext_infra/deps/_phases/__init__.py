# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Phase modules for pyproject dependency detector standardization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps._phases import (
        consolidate_groups as consolidate_groups,
        ensure_coverage as ensure_coverage,
        ensure_extra_paths as ensure_extra_paths,
        ensure_formatting as ensure_formatting,
        ensure_mypy as ensure_mypy,
        ensure_namespace as ensure_namespace,
        ensure_pydantic_mypy as ensure_pydantic_mypy,
        ensure_pyrefly as ensure_pyrefly,
        ensure_pyright as ensure_pyright,
        ensure_pytest as ensure_pytest,
        ensure_ruff as ensure_ruff,
        inject_comments as inject_comments,
    )
    from flext_infra.deps._phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps._phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps._phases.ensure_extra_paths import (
        FlextInfraEnsureExtraPathsPhase as FlextInfraEnsureExtraPathsPhase,
    )
    from flext_infra.deps._phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps._phases.ensure_mypy import (
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pytest import (
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps._phases.ensure_ruff import (
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps._phases.inject_comments import (
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraConsolidateGroupsPhase": [
        "flext_infra.deps._phases.consolidate_groups",
        "FlextInfraConsolidateGroupsPhase",
    ],
    "FlextInfraEnsureCoverageConfigPhase": [
        "flext_infra.deps._phases.ensure_coverage",
        "FlextInfraEnsureCoverageConfigPhase",
    ],
    "FlextInfraEnsureExtraPathsPhase": [
        "flext_infra.deps._phases.ensure_extra_paths",
        "FlextInfraEnsureExtraPathsPhase",
    ],
    "FlextInfraEnsureFormattingToolingPhase": [
        "flext_infra.deps._phases.ensure_formatting",
        "FlextInfraEnsureFormattingToolingPhase",
    ],
    "FlextInfraEnsureMypyConfigPhase": [
        "flext_infra.deps._phases.ensure_mypy",
        "FlextInfraEnsureMypyConfigPhase",
    ],
    "FlextInfraEnsureNamespaceToolingPhase": [
        "flext_infra.deps._phases.ensure_namespace",
        "FlextInfraEnsureNamespaceToolingPhase",
    ],
    "FlextInfraEnsurePydanticMypyConfigPhase": [
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "FlextInfraEnsurePydanticMypyConfigPhase",
    ],
    "FlextInfraEnsurePyreflyConfigPhase": [
        "flext_infra.deps._phases.ensure_pyrefly",
        "FlextInfraEnsurePyreflyConfigPhase",
    ],
    "FlextInfraEnsurePyrightConfigPhase": [
        "flext_infra.deps._phases.ensure_pyright",
        "FlextInfraEnsurePyrightConfigPhase",
    ],
    "FlextInfraEnsurePytestConfigPhase": [
        "flext_infra.deps._phases.ensure_pytest",
        "FlextInfraEnsurePytestConfigPhase",
    ],
    "FlextInfraEnsureRuffConfigPhase": [
        "flext_infra.deps._phases.ensure_ruff",
        "FlextInfraEnsureRuffConfigPhase",
    ],
    "FlextInfraInjectCommentsPhase": [
        "flext_infra.deps._phases.inject_comments",
        "FlextInfraInjectCommentsPhase",
    ],
    "consolidate_groups": ["flext_infra.deps._phases.consolidate_groups", ""],
    "ensure_coverage": ["flext_infra.deps._phases.ensure_coverage", ""],
    "ensure_extra_paths": ["flext_infra.deps._phases.ensure_extra_paths", ""],
    "ensure_formatting": ["flext_infra.deps._phases.ensure_formatting", ""],
    "ensure_mypy": ["flext_infra.deps._phases.ensure_mypy", ""],
    "ensure_namespace": ["flext_infra.deps._phases.ensure_namespace", ""],
    "ensure_pydantic_mypy": ["flext_infra.deps._phases.ensure_pydantic_mypy", ""],
    "ensure_pyrefly": ["flext_infra.deps._phases.ensure_pyrefly", ""],
    "ensure_pyright": ["flext_infra.deps._phases.ensure_pyright", ""],
    "ensure_pytest": ["flext_infra.deps._phases.ensure_pytest", ""],
    "ensure_ruff": ["flext_infra.deps._phases.ensure_ruff", ""],
    "inject_comments": ["flext_infra.deps._phases.inject_comments", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureExtraPathsPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
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
    "ensure_pytest",
    "ensure_ruff",
    "inject_comments",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
