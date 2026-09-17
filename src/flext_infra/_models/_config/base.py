"""Config models facade: joins the domain modules via MRO."""

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
    FlextInfraConfigModelsArtifact,
    FlextInfraConfigModelsBeads,
    FlextInfraConfigModelsContexts,
    FlextInfraConfigModelsContract,
    FlextInfraConfigModelsMake,
    FlextInfraConfigModelsProvider,
    FlextInfraConfigModelsRender,
    FlextInfraConfigModelsScaffold,
    FlextInfraConfigModelsStatic,
    FlextInfraConfigModelsTemplates,
    FlextInfraConfigModelsWorkspace,
):
    class Infra(FlextInfraConfigModelsInfra.Infra):
        """Typed settings namespace declared by the physical config family."""
