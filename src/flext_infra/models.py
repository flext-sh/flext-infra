"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m as _cli_m
from flext_infra import (
    FlextInfraBasemkModels,
    FlextInfraCheckModels,
    FlextInfraCodegenModels,
    FlextInfraCoreModels,
    FlextInfraDepsModels,
    FlextInfraDocsModels,
    FlextInfraEngineModels,
    FlextInfraGatesModels,
    FlextInfraGithubModels,
    FlextInfraModelsBase,
    FlextInfraModelsCensus,
    FlextInfraModelsCliInputs,
    FlextInfraModelsRope,
    FlextInfraModelsScan,
    FlextInfraRefactorModels,
    FlextInfraReleaseModels,
    FlextInfraWorkspaceModels,
)


class FlextInfraModels(_cli_m):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraModelsCliInputs,
        FlextInfraModelsCensus,
        FlextInfraBasemkModels,
        FlextInfraCheckModels,
        FlextInfraCodegenModels,
        FlextInfraDepsModels,
        FlextInfraDocsModels,
        FlextInfraGatesModels,
        FlextInfraGithubModels,
        FlextInfraRefactorModels,
        FlextInfraReleaseModels,
        FlextInfraCoreModels,
        FlextInfraWorkspaceModels,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        FlextInfraModelsBase,
        FlextInfraEngineModels,
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__ = ["FlextInfraModels", "m"]
