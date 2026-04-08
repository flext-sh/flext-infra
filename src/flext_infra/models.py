"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m
from flext_infra._models.base import FlextInfraModelsBase
from flext_infra._models.basemk import FlextInfraBasemkModels
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.check import FlextInfraCheckModels
from flext_infra._models.codegen import FlextInfraCodegenModels
from flext_infra._models.deps import FlextInfraDepsModels
from flext_infra._models.docs import FlextInfraDocsModels
from flext_infra._models.engine import FlextInfraEngineModels
from flext_infra._models.gates import FlextInfraGatesModels
from flext_infra._models.github import FlextInfraGithubModels
from flext_infra._models.refactor import FlextInfraRefactorModels
from flext_infra._models.release import FlextInfraReleaseModels
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.scan import FlextInfraModelsScan
from flext_infra._models.validate import FlextInfraCoreModels
from flext_infra._models.workspace import FlextInfraWorkspaceModels


class FlextInfraModels(m):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
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
