"""Config models base: composes every config family via MRO in dependency order.

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
from flext_infra._models._config.external_cache import (
    FlextInfraExternalCacheDirectorySpec,
)


class FlextInfraModelsConfig(
    FlextInfraModelsConfigContract,
    FlextInfraExternalCacheDirectorySpec,
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
    """Every config family joined in dependency order, foundations first."""


__all__: list[str] = ["FlextInfraModelsConfig"]
