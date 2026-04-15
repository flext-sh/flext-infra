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
    FlextInfraModelsDeps,
    FlextInfraModelsDocs,
    FlextInfraModelsEngine,
    FlextInfraModelsGates,
    FlextInfraModelsGithub,
    FlextInfraModelsMixins,
    FlextInfraModelsRefactor,
    FlextInfraModelsRelease,
    FlextInfraModelsRope,
    FlextInfraModelsScan,
    FlextInfraModelsWorkspace,
)


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
        FlextInfraModelsRefactor,
        FlextInfraModelsRelease,
        FlextInfraModelsMixins,
        FlextInfraModelsWorkspace,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        FlextInfraModelsBase,
        FlextInfraModelsEngine,
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__: list[str] = ["FlextInfraModels", "m"]
