# AUTO-GENERATED FILE — Regenerate with: make gen
"""config package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._config.artifact import FlextInfraModelsConfigArtifact
    from flext_infra._config.base import FlextInfraModelsConfig
    from flext_infra._config.beads import FlextInfraModelsConfigBeads
    from flext_infra._config.contexts import FlextInfraModelsConfigContexts
    from flext_infra._config.contract import FlextInfraModelsConfigContract
    from flext_infra._config.external_cache import FlextInfraExternalCacheDirectorySpec
    from flext_infra._config.make import FlextInfraModelsConfigMake
    from flext_infra._config.make_clean import FlextInfraModelsConfigMakeClean
    from flext_infra._config.make_docs import FlextInfraModelsConfigMakeDocs
    from flext_infra._config.provider import FlextInfraModelsConfigProvider
    from flext_infra._config.refactor_campaigns import (
        FlextInfraModelsConfigRefactorCampaigns,
    )
    from flext_infra._config.release import FlextInfraModelsConfigRelease
    from flext_infra._config.render import FlextInfraModelsConfigRender
    from flext_infra._config.repository import FlextInfraModelsConfigRepository
    from flext_infra._config.root import FlextInfraModelsConfigRoot
    from flext_infra._config.scaffold import FlextInfraModelsConfigScaffold
    from flext_infra._config.sonarcloud import FlextInfraModelsConfigSonarcloud
    from flext_infra._config.static import FlextInfraModelsConfigStatic
    from flext_infra._config.templates import FlextInfraModelsConfigTemplates
    from flext_infra._config.workspace import FlextInfraModelsConfigWorkspace


__all__: tuple[str, ...] = (
    "FlextInfraExternalCacheDirectorySpec",
    "FlextInfraModelsConfig",
    "FlextInfraModelsConfigArtifact",
    "FlextInfraModelsConfigBeads",
    "FlextInfraModelsConfigContexts",
    "FlextInfraModelsConfigContract",
    "FlextInfraModelsConfigMake",
    "FlextInfraModelsConfigMakeClean",
    "FlextInfraModelsConfigMakeDocs",
    "FlextInfraModelsConfigProvider",
    "FlextInfraModelsConfigRefactorCampaigns",
    "FlextInfraModelsConfigRelease",
    "FlextInfraModelsConfigRender",
    "FlextInfraModelsConfigRepository",
    "FlextInfraModelsConfigRoot",
    "FlextInfraModelsConfigScaffold",
    "FlextInfraModelsConfigSonarcloud",
    "FlextInfraModelsConfigStatic",
    "FlextInfraModelsConfigTemplates",
    "FlextInfraModelsConfigWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraModelsConfig": ".base",
        "FlextInfraModelsConfigArtifact": ".artifact",
        "FlextInfraModelsConfigBeads": ".beads",
        "FlextInfraModelsConfigContexts": ".contexts",
        "FlextInfraModelsConfigContract": ".contract",
        "FlextInfraModelsConfigMake": ".make",
        "FlextInfraModelsConfigMakeClean": ".make_clean",
        "FlextInfraModelsConfigMakeDocs": ".make_docs",
        "FlextInfraModelsConfigProvider": ".provider",
        "FlextInfraModelsConfigRefactorCampaigns": ".refactor_campaigns",
        "FlextInfraModelsConfigRelease": ".release",
        "FlextInfraModelsConfigRender": ".render",
        "FlextInfraModelsConfigRepository": ".repository",
        "FlextInfraModelsConfigRoot": ".root",
        "FlextInfraModelsConfigScaffold": ".scaffold",
        "FlextInfraModelsConfigSonarcloud": ".sonarcloud",
        "FlextInfraModelsConfigStatic": ".static",
        "FlextInfraModelsConfigTemplates": ".templates",
        "FlextInfraModelsConfigWorkspace": ".workspace",
        "FlextInfraExternalCacheDirectorySpec": ".external_cache",
    }),
    public_exports=__all__,
)
