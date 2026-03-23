"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core import FlextModels

from flext_infra import (
    FlextInfraBasemkModels,
    FlextInfraCheckModels,
    FlextInfraCodegenModels,
    FlextInfraCoreModels,
    FlextInfraDepsModels,
    FlextInfraDocsModels,
    FlextInfraGatesModels,
    FlextInfraGithubModels,
    FlextInfraRefactorModels,
    FlextInfraReleaseModels,
    FlextInfraUtilitiesModels,
    FlextInfraWorkspaceModels,
)


class FlextInfraModels(FlextModels):
    class Infra(
        FlextInfraUtilitiesModels,
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
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__ = ["FlextInfraModels", "m"]
