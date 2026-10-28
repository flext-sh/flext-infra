"""Config models base: composes every config family via MRO in dependency order.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra._models._config.artifact import FlextInfraModelsConfigArtifact
from flext_infra._models._config.beads import FlextInfraModelsConfigBeads
from flext_infra._models._config.contexts import FlextInfraModelsConfigContexts
from flext_infra._models._config.contract import FlextInfraModelsConfigContract
from flext_infra._models._config.make import FlextInfraModelsConfigMake
from flext_infra._models._config.provider import FlextInfraModelsConfigProvider
from flext_infra._models._config.release import FlextInfraModelsConfigRelease
from flext_infra._models._config.render import FlextInfraModelsConfigRender
from flext_infra._models._config.root import FlextInfraModelsConfigRoot
from flext_infra._models._config.scaffold import FlextInfraModelsConfigScaffold
from flext_infra._models._config.static import FlextInfraModelsConfigStatic
from flext_infra._models._config.templates import FlextInfraModelsConfigTemplates
from flext_infra._models._config.workspace import FlextInfraModelsConfigWorkspace


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
    """Every config family joined in dependency order, foundations first."""


__all__: list[str] = ["FlextInfraModelsConfig"]
