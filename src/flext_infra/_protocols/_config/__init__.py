# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Protocols. Config package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols._config.artifact import (
        FlextInfraProtocolsConfigArtifact,
    )
    from flext_infra._protocols._config.beads import FlextInfraProtocolsConfigBeads
    from flext_infra._protocols._config.contexts import (
        FlextInfraProtocolsConfigContexts,
    )
    from flext_infra._protocols._config.contract import (
        FlextInfraProtocolsConfigContract,
    )
    from flext_infra._protocols._config.external_cache import (
        FlextInfraProtocolsConfigExternalCache,
    )
    from flext_infra._protocols._config.make import FlextInfraProtocolsConfigMake
    from flext_infra._protocols._config.make_clean import (
        FlextInfraProtocolsConfigMakeClean,
    )
    from flext_infra._protocols._config.make_docs import (
        FlextInfraProtocolsConfigMakeDocs,
    )
    from flext_infra._protocols._config.provider import (
        FlextInfraProtocolsConfigProvider,
    )
    from flext_infra._protocols._config.refactor_campaigns import (
        FlextInfraProtocolsConfigRefactorCampaigns,
    )
    from flext_infra._protocols._config.release import FlextInfraProtocolsConfigRelease
    from flext_infra._protocols._config.render import FlextInfraProtocolsConfigRender
    from flext_infra._protocols._config.repository import (
        FlextInfraProtocolsConfigRepository,
    )
    from flext_infra._protocols._config.root import FlextInfraProtocolsConfigRoot
    from flext_infra._protocols._config.scaffold import (
        FlextInfraProtocolsConfigScaffold,
    )
    from flext_infra._protocols._config.sonarcloud import (
        FlextInfraProtocolsConfigSonarcloud,
    )
    from flext_infra._protocols._config.static import FlextInfraProtocolsConfigStatic
    from flext_infra._protocols._config.templates import (
        FlextInfraProtocolsConfigTemplates,
    )
    from flext_infra._protocols._config.workspace import (
        FlextInfraProtocolsConfigWorkspace,
    )


__all__: tuple[str, ...] = (
    "FlextInfraProtocolsConfigArtifact",
    "FlextInfraProtocolsConfigBeads",
    "FlextInfraProtocolsConfigContexts",
    "FlextInfraProtocolsConfigContract",
    "FlextInfraProtocolsConfigExternalCache",
    "FlextInfraProtocolsConfigMake",
    "FlextInfraProtocolsConfigMakeClean",
    "FlextInfraProtocolsConfigMakeDocs",
    "FlextInfraProtocolsConfigProvider",
    "FlextInfraProtocolsConfigRefactorCampaigns",
    "FlextInfraProtocolsConfigRelease",
    "FlextInfraProtocolsConfigRender",
    "FlextInfraProtocolsConfigRepository",
    "FlextInfraProtocolsConfigRoot",
    "FlextInfraProtocolsConfigScaffold",
    "FlextInfraProtocolsConfigSonarcloud",
    "FlextInfraProtocolsConfigStatic",
    "FlextInfraProtocolsConfigTemplates",
    "FlextInfraProtocolsConfigWorkspace",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraProtocolsConfigArtifact": ".artifact",
        "FlextInfraProtocolsConfigBeads": ".beads",
        "FlextInfraProtocolsConfigContexts": ".contexts",
        "FlextInfraProtocolsConfigContract": ".contract",
        "FlextInfraProtocolsConfigExternalCache": ".external_cache",
        "FlextInfraProtocolsConfigMake": ".make",
        "FlextInfraProtocolsConfigMakeClean": ".make_clean",
        "FlextInfraProtocolsConfigMakeDocs": ".make_docs",
        "FlextInfraProtocolsConfigProvider": ".provider",
        "FlextInfraProtocolsConfigRefactorCampaigns": ".refactor_campaigns",
        "FlextInfraProtocolsConfigRelease": ".release",
        "FlextInfraProtocolsConfigRender": ".render",
        "FlextInfraProtocolsConfigRepository": ".repository",
        "FlextInfraProtocolsConfigRoot": ".root",
        "FlextInfraProtocolsConfigScaffold": ".scaffold",
        "FlextInfraProtocolsConfigSonarcloud": ".sonarcloud",
        "FlextInfraProtocolsConfigStatic": ".static",
        "FlextInfraProtocolsConfigTemplates": ".templates",
        "FlextInfraProtocolsConfigWorkspace": ".workspace",
    }),
    public_exports=__all__,
)
