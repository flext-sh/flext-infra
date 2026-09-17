"""Config models base: composes every config family via MRO in dependency order."""

from __future__ import annotations

from .artifact import FlextInfraConfigModelsArtifact
from .beads import FlextInfraConfigModelsBeads
from .contexts import FlextInfraConfigModelsContexts
from .contract import FlextInfraConfigModelsContract
from .infra import FlextInfraConfigModelsInfra
from .make import FlextInfraConfigModelsMake
from .provider import FlextInfraConfigModelsProvider
from .render import FlextInfraConfigModelsRender
from .scaffold import FlextInfraConfigModelsScaffold
from .static import FlextInfraConfigModelsStatic
from .templates import FlextInfraConfigModelsTemplates
from .workspace import FlextInfraConfigModelsWorkspace


class FlextInfraConfigModels(
    FlextInfraConfigModelsContract,
    FlextInfraConfigModelsProvider,
    FlextInfraConfigModelsScaffold,
    FlextInfraConfigModelsStatic,
    FlextInfraConfigModelsMake,
    FlextInfraConfigModelsBeads,
    FlextInfraConfigModelsTemplates,
    FlextInfraConfigModelsContexts,
    FlextInfraConfigModelsRender,
    FlextInfraConfigModelsWorkspace,
    FlextInfraConfigModelsArtifact,
):
    """Every config family joined in dependency order, foundations first."""

    class Infra(FlextInfraConfigModelsInfra.Infra):
        """Typed settings namespace declared by the physical config family."""
