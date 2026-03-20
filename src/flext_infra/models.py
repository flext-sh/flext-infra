"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_core import FlextModels
from flext_infra._utilities._models import FlextInfraUtilitiesModels
from flext_infra.basemk._models import FlextInfraBasemkModels
from flext_infra.check._models import FlextInfraCheckModels
from flext_infra.codegen._models import FlextInfraCodegenModels
from flext_infra.deps._models import FlextInfraDepsModels
from flext_infra.docs._models import FlextInfraDocsModels
from flext_infra.github._models import FlextInfraGithubModels
from flext_infra.refactor._models import FlextInfraRefactorModels
from flext_infra.release._models import FlextInfraReleaseModels
from flext_infra.validate._models import FlextInfraCoreModels
from flext_infra.workspace._models import FlextInfraWorkspaceModels


class FlextInfraModels(FlextModels):
    class Infra(
        FlextInfraUtilitiesModels,
        FlextInfraBasemkModels,
        FlextInfraCheckModels,
        FlextInfraCodegenModels,
        FlextInfraDepsModels,
        FlextInfraDocsModels,
        FlextInfraGithubModels,
        FlextInfraRefactorModels,
        FlextInfraReleaseModels,
        FlextInfraCoreModels,
        FlextInfraWorkspaceModels,
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__ = ["FlextInfraModels", "m"]
