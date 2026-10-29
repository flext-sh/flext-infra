"""Config models composition for the infrastructure namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra._models._config import (
    FlextInfraModelsConfigArtifact,
    FlextInfraModelsConfigBeads,
    FlextInfraModelsConfigContexts,
    FlextInfraModelsConfigContract,
    FlextInfraModelsConfigMake,
    FlextInfraModelsConfigProvider,
    FlextInfraModelsConfigRelease,
    FlextInfraModelsConfigRender,
    FlextInfraModelsConfigRoot,
    FlextInfraModelsConfigScaffold,
    FlextInfraModelsConfigStatic,
    FlextInfraModelsConfigTemplates,
    FlextInfraModelsConfigWorkspace,
)


class FlextInfraModelsConfig(
    FlextInfraModelsConfigContract,
    FlextInfraModelsConfigProvider,
    FlextInfraModelsConfigRender,
    FlextInfraModelsConfigRoot,
    FlextInfraModelsConfigScaffold,
    FlextInfraModelsConfigStatic,
    FlextInfraModelsConfigMake,
    FlextInfraModelsConfigBeads,
    FlextInfraModelsConfigTemplates,
    FlextInfraModelsConfigContexts,
    FlextInfraModelsConfigWorkspace,
    FlextInfraModelsConfigRelease,
    FlextInfraModelsConfigArtifact,
):
    """Config models composition for the infrastructure namespace."""


__all__: list[str] = ["FlextInfraModelsConfig"]
