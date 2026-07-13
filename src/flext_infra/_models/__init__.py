# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Models package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra._models.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra._models.base import FlextInfraModelsBase as FlextInfraModelsBase
    from flext_infra._models.basemk import (
        FlextInfraModelsBasemk as FlextInfraModelsBasemk,
    )
    from flext_infra._models.census import (
        FlextInfraModelsCensus as FlextInfraModelsCensus,
    )
    from flext_infra._models.check import FlextInfraModelsCheck as FlextInfraModelsCheck
    from flext_infra._models.codegen import (
        FlextInfraModelsCodegen as FlextInfraModelsCodegen,
    )
    from flext_infra._models.codegen_render import (
        FlextInfraModelsCodegenRender as FlextInfraModelsCodegenRender,
    )
    from flext_infra._models.config import (
        FlextInfraConfigModels as FlextInfraConfigModels,
    )
    from flext_infra._models.deps import FlextInfraModelsDeps as FlextInfraModelsDeps
    from flext_infra._models.deps_toml import (
        FlextInfraModelsDepsToml as FlextInfraModelsDepsToml,
    )
    from flext_infra._models.deps_tool_config import (
        FlextInfraModelsDepsToolSettings as FlextInfraModelsDepsToolSettings,
    )
    from flext_infra._models.deps_tool_config_linters import (
        FlextInfraModelsDepsToolConfigLinters as FlextInfraModelsDepsToolConfigLinters,
    )
    from flext_infra._models.deps_tool_config_type_checkers import (
        FlextInfraModelsDepsToolConfigTypeCheckers as FlextInfraModelsDepsToolConfigTypeCheckers,
    )
    from flext_infra._models.docs import FlextInfraModelsDocs as FlextInfraModelsDocs

    # NOTE (multi-agent, cosmos-main-15bi): enforcement/transformers facades
    # hand-added in the gen format; `make gen` converges to this same content.
    from flext_infra._models.enforcement import (
        FlextInfraModelsEnforcement as FlextInfraModelsEnforcement,
    )
    from flext_infra._models.gates import FlextInfraModelsGates as FlextInfraModelsGates
    from flext_infra._models.github import (
        FlextInfraModelsGithub as FlextInfraModelsGithub,
    )
    from flext_infra._models.mixins import (
        FlextInfraModelsMixins as FlextInfraModelsMixins,
    )
    from flext_infra._models.mro_scan import (
        FlextInfraModelsMroScan as FlextInfraModelsMroScan,
    )
    from flext_infra._models.refactor import (
        FlextInfraModelsRefactor as FlextInfraModelsRefactor,
    )
    from flext_infra._models.refactor_ast_grep import (
        FlextInfraModelsRefactorGrep as FlextInfraModelsRefactorGrep,
    )
    from flext_infra._models.refactor_census import (
        FlextInfraModelsRefactorCensus as FlextInfraModelsRefactorCensus,
    )
    from flext_infra._models.refactor_namespace_enforcer import (
        FlextInfraModelsNamespaceEnforcer as FlextInfraModelsNamespaceEnforcer,
    )
    from flext_infra._models.refactor_violations import (
        FlextInfraModelsRefactorViolations as FlextInfraModelsRefactorViolations,
    )
    from flext_infra._models.release import (
        FlextInfraModelsRelease as FlextInfraModelsRelease,
    )
    from flext_infra._models.rope import FlextInfraModelsRope as FlextInfraModelsRope
    from flext_infra._models.scan import FlextInfraModelsScan as FlextInfraModelsScan
    from flext_infra._models.settings import (
        FlextInfraSettingsModels as FlextInfraSettingsModels,
    )
    from flext_infra._models.transformers import (
        FlextInfraModelsTransformers as FlextInfraModelsTransformers,
    )
    from flext_infra._models.validate import (
        FlextInfraModelsCore as FlextInfraModelsCore,
    )
    from flext_infra._models.workspace import (
        FlextInfraModelsWorkspace as FlextInfraModelsWorkspace,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
