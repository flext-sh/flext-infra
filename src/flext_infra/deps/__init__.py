# AUTO-GENERATED FILE — Regenerate with: make gen
"""Deps package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps._detection.runners import FlextInfraDepsDetectionRunners
    from flext_infra.deps._detector.runtime_steps import (
        FlextInfraDepsDetectorRuntimeSteps,
    )
    from flext_infra.deps._modernizer.base import FlextInfraPyprojectModernizerBase
    from flext_infra.deps._modernizer.document import (
        FlextInfraPyprojectModernizerDocument,
    )
    from flext_infra.deps._modernizer.run import FlextInfraPyprojectModernizerRun
    from flext_infra.deps._modernizer.tooling import (
        FlextInfraPyprojectModernizerTooling,
    )
    from flext_infra.deps._pyrefly.fix_steps import FlextInfraDepsPyreflyFixSteps
    from flext_infra.deps.detection import FlextInfraDependencyDetectionService
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
    from flext_infra.deps.detector_runtime import FlextInfraDependencyDetectorRuntime
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
    from flext_infra.deps.lock_integrity import FlextInfraLockIntegrityVerifier
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
    from flext_infra.deps.phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps.phases.ensure_packaging import FlextInfraEnsurePackagingPhase
    from flext_infra.deps.phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps.phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase
    from flext_infra.deps.phases.tool_tables import FlextInfraToolTablesPhase
    from flext_infra.deps.pyrefly import FlextInfraDepsPyrefly


__all__: tuple[str, ...] = (
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDepsDetectionRunners",
    "FlextInfraDepsDetectorRuntimeSteps",
    "FlextInfraDepsPyrefly",
    "FlextInfraDepsPyreflyFixSteps",
    "FlextInfraEnsurePackagingPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraLockIntegrityVerifier",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyprojectModernizerBase",
    "FlextInfraPyprojectModernizerDocument",
    "FlextInfraPyprojectModernizerRun",
    "FlextInfraPyprojectModernizerTooling",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraToolTablesPhase",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraConfigFixer": ".fix_pyrefly_config",
        "FlextInfraConsolidateGroupsPhase": ".phases.consolidate_groups",
        "FlextInfraDependencyDetectionService": ".detection",
        "FlextInfraDependencyDetectorRuntime": ".detector_runtime",
        "FlextInfraDepsDetectionRunners": "._detection.runners",
        "FlextInfraDepsDetectorRuntimeSteps": "._detector.runtime_steps",
        "FlextInfraDepsPyrefly": ".pyrefly",
        "FlextInfraDepsPyreflyFixSteps": "._pyrefly.fix_steps",
        "FlextInfraEnsurePackagingPhase": ".phases.ensure_packaging",
        "FlextInfraEnsurePyreflyConfigPhase": ".phases.ensure_pyrefly",
        "FlextInfraEnsurePyrightConfigPhase": ".phases.ensure_pyright",
        "FlextInfraEnsureRuffConfigPhase": ".phases.ensure_ruff",
        "FlextInfraExtraPathsManager": ".extra_paths",
        "FlextInfraInjectCommentsPhase": ".phases.inject_comments",
        "FlextInfraLockIntegrityVerifier": ".lock_integrity",
        "FlextInfraPyprojectModernizer": ".modernizer",
        "FlextInfraPyprojectModernizerBase": "._modernizer.base",
        "FlextInfraPyprojectModernizerDocument": "._modernizer.document",
        "FlextInfraPyprojectModernizerRun": "._modernizer.run",
        "FlextInfraPyprojectModernizerTooling": "._modernizer.tooling",
        "FlextInfraRuntimeDevDependencyDetector": ".detector",
        "FlextInfraToolTablesPhase": ".phases.tool_tables",
    }),
    public_exports=__all__,
)
