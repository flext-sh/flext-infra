"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m

from flext_infra import (
    FlextInfraModelsBase,
    FlextInfraModelsBasemk,
    FlextInfraModelsCensus,
    FlextInfraModelsCheck,
    FlextInfraModelsCodegen,
    FlextInfraModelsCore,
    FlextInfraModelsDeps,
    FlextInfraModelsDocs,
    FlextInfraModelsEngine,
    FlextInfraModelsGates,
    FlextInfraModelsGithub,
    FlextInfraModelsGuard,
    FlextInfraModelsMixins,
    FlextInfraModelsRefactor,
    FlextInfraModelsRelease,
    FlextInfraModelsRope,
    FlextInfraModelsScan,
    FlextInfraModelsWorkspace,
)
from flext_infra._models.scope import FlextInfraModelsScope


class FlextInfraModels(m):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraModelsCensus,
        FlextInfraModelsBasemk,
        FlextInfraModelsCheck,
        FlextInfraModelsCodegen,
        FlextInfraModelsDeps,
        FlextInfraModelsDocs,
        FlextInfraModelsGates,
        FlextInfraModelsGithub,
        FlextInfraModelsGuard,
        FlextInfraModelsRefactor,
        FlextInfraModelsRelease,
        FlextInfraModelsMixins,
        FlextInfraModelsWorkspace,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        FlextInfraModelsScope,
        FlextInfraModelsCore,
        FlextInfraModelsBase,
        FlextInfraModelsEngine,
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__: list[str] = ["FlextInfraModels", "m"]
