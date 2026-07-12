"""Domain models for flext-infra.

Defines data models and domain entities for infrastructure services including
configuration, validation results, and workspace state.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import m

from flext_infra._models.base import FlextInfraModelsBase
from flext_infra._models.basemk import FlextInfraModelsBasemk
from flext_infra._models.census import FlextInfraModelsCensus
from flext_infra._models.check import FlextInfraModelsCheck
from flext_infra._models.codegen import FlextInfraModelsCodegen
from flext_infra._models.config import FlextInfraConfigModels
from flext_infra._models.deps import FlextInfraModelsDeps
from flext_infra._models.docs import FlextInfraModelsDocs
from flext_infra._models.enforcement import FlextInfraModelsEnforcement
from flext_infra._models.gates import FlextInfraModelsGates
from flext_infra._models.github import FlextInfraModelsGithub
from flext_infra._models.mixins import FlextInfraModelsMixins
from flext_infra._models.refactor import FlextInfraModelsRefactor
from flext_infra._models.release import FlextInfraModelsRelease
from flext_infra._models.rope import FlextInfraModelsRope
from flext_infra._models.scan import FlextInfraModelsScan
from flext_infra._models.transformers import FlextInfraModelsTransformers
from flext_infra._models.validate import FlextInfraModelsCore
from flext_infra._models.workspace import FlextInfraModelsWorkspace


class FlextInfraModels(m):
    """Merged model namespace for flext-infra domain objects."""

    class Infra(
        FlextInfraModelsCensus,
        FlextInfraModelsBasemk,
        FlextInfraModelsCheck,
        # NOTE (multi-agent, mro-wkii.17 / agent: codex): conform contracts are
        # isolated from the active detector work in _models/codegen.py while
        # remaining exposed through the single public m.Infra facade.
        FlextInfraConfigModels,
        FlextInfraModelsCodegen,
        FlextInfraModelsDeps,
        FlextInfraModelsDocs,
        # NOTE (multi-agent, cosmos-main-15bi): enforcement/transformers model
        # facades added for the deep-FLEXT dataclass -> m.Infra migration.
        FlextInfraModelsEnforcement,
        FlextInfraModelsGates,
        FlextInfraModelsGithub,
        FlextInfraModelsRefactor,
        FlextInfraModelsRelease,
        FlextInfraModelsMixins,
        FlextInfraModelsTransformers,
        FlextInfraModelsWorkspace,
        FlextInfraModelsRope,
        FlextInfraModelsScan,
        FlextInfraModelsCore,
        FlextInfraModelsBase,
    ):
        """Infrastructure-domain models - all classes exposed directly."""


m = FlextInfraModels

__all__: list[str] = ["FlextInfraModels", "m"]
