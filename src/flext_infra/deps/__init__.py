# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Dependency management services.

Provides the pyproject modernizer for workspace-wide dependency
synchronization and formatting.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps import (
        _phases,
        cli,
        detection,
        detector,
        extra_paths,
        fix_pyrefly_config,
        internal_sync,
        modernizer,
        path_sync,
    )
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
    from flext_infra.deps._phases.consolidate_groups import *
    from flext_infra.deps._phases.ensure_coverage import *
    from flext_infra.deps._phases.ensure_extra_paths import *
    from flext_infra.deps._phases.ensure_formatting import *
    from flext_infra.deps._phases.ensure_mypy import *
    from flext_infra.deps._phases.ensure_namespace import *
    from flext_infra.deps._phases.ensure_pydantic_mypy import *
    from flext_infra.deps._phases.ensure_pyrefly import *
    from flext_infra.deps._phases.ensure_pyright import *
    from flext_infra.deps._phases.ensure_pytest import *
    from flext_infra.deps._phases.ensure_ruff import *
    from flext_infra.deps._phases.inject_comments import *
    from flext_infra.deps.cli import *
    from flext_infra.deps.detection import *
    from flext_infra.deps.detector import *
    from flext_infra.deps.extra_paths import *
    from flext_infra.deps.fix_pyrefly_config import *
    from flext_infra.deps.internal_sync import *
    from flext_infra.deps.modernizer import *
    from flext_infra.deps.path_sync import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraCliDeps": "flext_infra.deps.cli",
    "FlextInfraConfigFixer": "flext_infra.deps.fix_pyrefly_config",
    "FlextInfraConsolidateGroupsPhase": "flext_infra.deps._phases.consolidate_groups",
    "FlextInfraDependencyDetectionService": "flext_infra.deps.detection",
    "FlextInfraDependencyPathSync": "flext_infra.deps.path_sync",
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
    "FlextInfraExtraPathsManager": "flext_infra.deps.extra_paths",
    "FlextInfraInjectCommentsPhase": "flext_infra.deps._phases.inject_comments",
    "FlextInfraInternalDependencySyncService": "flext_infra.deps.internal_sync",
    "FlextInfraPyprojectModernizer": "flext_infra.deps.modernizer",
    "FlextInfraRuntimeDevDependencyDetector": "flext_infra.deps.detector",
    "_phases": "flext_infra.deps._phases",
    "cli": "flext_infra.deps.cli",
    "consolidate_groups": "flext_infra.deps._phases.consolidate_groups",
    "detection": "flext_infra.deps.detection",
    "detector": "flext_infra.deps.detector",
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
    "extra_paths": "flext_infra.deps.extra_paths",
    "fix_pyrefly_config": "flext_infra.deps.fix_pyrefly_config",
    "inject_comments": "flext_infra.deps._phases.inject_comments",
    "internal_sync": "flext_infra.deps.internal_sync",
    "main": "flext_infra.deps.detector",
    "modernizer": "flext_infra.deps.modernizer",
    "path_sync": "flext_infra.deps.path_sync",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
