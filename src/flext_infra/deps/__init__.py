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
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _TYPE_CHECKING:
    from flext_infra.deps._constants import *
    from flext_infra.deps._detector_runtime import *
    from flext_infra.deps._models import *
    from flext_infra.deps._phases import *
    from flext_infra.deps.cli import *
    from flext_infra.deps.detection import *
    from flext_infra.deps.detector import *
    from flext_infra.deps.extra_paths import *
    from flext_infra.deps.fix_pyrefly_config import *
    from flext_infra.deps.internal_sync import *
    from flext_infra.deps.modernizer import *
    from flext_infra.deps.path_sync import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = merge_lazy_imports(
    ("flext_infra.deps._phases",),
    {
        "FlextInfraCliDeps": "flext_infra.deps.cli",
        "FlextInfraConfigFixer": "flext_infra.deps.fix_pyrefly_config",
        "FlextInfraDependencyDetectionService": "flext_infra.deps.detection",
        "FlextInfraDependencyDetectorRuntime": "flext_infra.deps._detector_runtime",
        "FlextInfraDependencyPathSync": "flext_infra.deps.path_sync",
        "FlextInfraDepsConstants": "flext_infra.deps._constants",
        "FlextInfraDepsModels": "flext_infra.deps._models",
        "FlextInfraExtraPathsManager": "flext_infra.deps.extra_paths",
        "FlextInfraInternalDependencySyncService": "flext_infra.deps.internal_sync",
        "FlextInfraPyprojectModernizer": "flext_infra.deps.modernizer",
        "FlextInfraRuntimeDevDependencyDetector": "flext_infra.deps.detector",
        "_constants": "flext_infra.deps._constants",
        "_detector_runtime": "flext_infra.deps._detector_runtime",
        "_models": "flext_infra.deps._models",
        "_phases": "flext_infra.deps._phases",
        "cli": "flext_infra.deps.cli",
        "detection": "flext_infra.deps.detection",
        "detector": "flext_infra.deps.detector",
        "extra_paths": "flext_infra.deps.extra_paths",
        "fix_pyrefly_config": "flext_infra.deps.fix_pyrefly_config",
        "internal_sync": "flext_infra.deps.internal_sync",
        "main": "flext_infra.deps.detector",
        "modernizer": "flext_infra.deps.modernizer",
        "path_sync": "flext_infra.deps.path_sync",
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
