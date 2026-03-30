"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import FlextCliModels

from flext_infra import (
    FlextInfraBasemkModels,
    FlextInfraCheckModels,
    FlextInfraCodegenModels,
    FlextInfraCoreModels,
    FlextInfraDepsModels,
    FlextInfraDocsModels,
    FlextInfraGatesModels,
    FlextInfraGithubModels,
    FlextInfraModelsBase,
    FlextInfraModelsCensus,
    FlextInfraModelsCliInputs,
    FlextInfraModelsCst,
    FlextInfraModelsRope,
    FlextInfraModelsScan,
    FlextInfraRefactorModels,
    FlextInfraReleaseModels,
    FlextInfraWorkspaceModels,
)


class FlextInfraModels(FlextCliModels):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraModelsCliInputs,
        FlextInfraModelsCensus,
        FlextInfraModelsCst,
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
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__ = ["FlextInfraModels", "m"]
