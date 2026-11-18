# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.deps.cooldown_admission import FlextInfraCooldownAdmission
    from flext_infra.deps.detection import FlextInfraDependencyDetectionService
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
    from flext_infra.deps.detector_runtime import FlextInfraDependencyDetectorRuntime
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
    from flext_infra.deps.lock_integrity import FlextInfraLockIntegrityVerifier
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
    from flext_infra.deps.pyrefly import FlextInfraDepsPyrefly


__all__: tuple[str, ...] = (
    "FlextInfraConfigFixer",
    "FlextInfraCooldownAdmission",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDepsPyrefly",
    "FlextInfraExtraPathsManager",
    "FlextInfraLockIntegrityVerifier",
    "FlextInfraPyprojectModernizer",
    "FlextInfraRuntimeDevDependencyDetector",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraConfigFixer": ".fix_pyrefly_config",
        "FlextInfraCooldownAdmission": ".cooldown_admission",
        "FlextInfraDependencyDetectionService": ".detection",
        "FlextInfraDependencyDetectorRuntime": ".detector_runtime",
        "FlextInfraDepsPyrefly": ".pyrefly",
        "FlextInfraExtraPathsManager": ".extra_paths",
        "FlextInfraLockIntegrityVerifier": ".lock_integrity",
        "FlextInfraPyprojectModernizer": ".modernizer",
        "FlextInfraRuntimeDevDependencyDetector": ".detector",
    },
    public_exports=__all__,
)
