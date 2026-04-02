# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release management services.

Provides services for versioning, release notes generation, and release
orchestration through composable phases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra.release import _constants, _models, cli, orchestrator
    from flext_infra.release._constants import FlextInfraReleaseConstants
    from flext_infra.release._models import FlextInfraReleaseModels
    from flext_infra.release.cli import FlextInfraCliRelease
    from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraCliRelease": "flext_infra.release.cli",
    "FlextInfraReleaseConstants": "flext_infra.release._constants",
    "FlextInfraReleaseModels": "flext_infra.release._models",
    "FlextInfraReleaseOrchestrator": "flext_infra.release.orchestrator",
    "_constants": "flext_infra.release._constants",
    "_models": "flext_infra.release._models",
    "cli": "flext_infra.release.cli",
    "orchestrator": "flext_infra.release.orchestrator",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
