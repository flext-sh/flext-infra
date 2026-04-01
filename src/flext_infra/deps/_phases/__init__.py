# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Phase modules for pyproject dependency detector standardization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.deps._phases import (
        consolidate_groups,
        ensure_coverage,
        ensure_extra_paths,
        ensure_formatting,
        ensure_mypy,
        ensure_namespace,
        ensure_pydantic_mypy,
        ensure_pyrefly,
        ensure_pyright,
        ensure_pytest,
        ensure_ruff,
        inject_comments,
    )
    from flext_infra.deps._phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps._phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps._phases.ensure_extra_paths import (
        FlextInfraEnsureExtraPathsPhase,
    )
    from flext_infra.deps._phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps._phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
    from flext_infra.deps._phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
    from flext_infra.deps._phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from flext_infra.deps._phases.inject_comments import FlextInfraInjectCommentsPhase

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraConsolidateGroupsPhase": "flext_infra.deps._phases.consolidate_groups",
    "FlextInfraEnsureCoverageConfigPhase": "flext_infra.deps._phases.ensure_coverage",
    "FlextInfraEnsureExtraPathsPhase": "flext_infra.deps._phases.ensure_extra_paths",
    "FlextInfraEnsureFormattingToolingPhase": "flext_infra.deps._phases.ensure_formatting",
    "FlextInfraEnsureMypyConfigPhase": "flext_infra.deps._phases.ensure_mypy",
    "FlextInfraEnsureNamespaceToolingPhase": "flext_infra.deps._phases.ensure_namespace",
    "FlextInfraEnsurePydanticMypyConfigPhase": "flext_infra.deps._phases.ensure_pydantic_mypy",
    "FlextInfraEnsurePyreflyConfigPhase": "flext_infra.deps._phases.ensure_pyrefly",
    "FlextInfraEnsurePyrightConfigPhase": "flext_infra.deps._phases.ensure_pyright",
    "FlextInfraEnsurePytestConfigPhase": "flext_infra.deps._phases.ensure_pytest",
    "FlextInfraEnsureRuffConfigPhase": "flext_infra.deps._phases.ensure_ruff",
    "FlextInfraInjectCommentsPhase": "flext_infra.deps._phases.inject_comments",
    "consolidate_groups": "flext_infra.deps._phases.consolidate_groups",
    "ensure_coverage": "flext_infra.deps._phases.ensure_coverage",
    "ensure_extra_paths": "flext_infra.deps._phases.ensure_extra_paths",
    "ensure_formatting": "flext_infra.deps._phases.ensure_formatting",
    "ensure_mypy": "flext_infra.deps._phases.ensure_mypy",
    "ensure_namespace": "flext_infra.deps._phases.ensure_namespace",
    "ensure_pydantic_mypy": "flext_infra.deps._phases.ensure_pydantic_mypy",
    "ensure_pyrefly": "flext_infra.deps._phases.ensure_pyrefly",
    "ensure_pyright": "flext_infra.deps._phases.ensure_pyright",
    "ensure_pytest": "flext_infra.deps._phases.ensure_pytest",
    "ensure_ruff": "flext_infra.deps._phases.ensure_ruff",
    "inject_comments": "flext_infra.deps._phases.inject_comments",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
