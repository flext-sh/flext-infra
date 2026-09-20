# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen. Conform package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from ._request_fields import FlextInfraCodegenConformRequestFields
    from .artifact_render import FlextInfraCodegenConformArtifactRender
    from .base import FlextInfraCodegenConformBase
    from .beads_routes import FlextInfraCodegenConformBeadsRoutes
    from .bootstrap import FlextInfraCodegenConformBootstrap
    from .context_render import FlextInfraCodegenConformContextRender
    from .docs_ownership import FlextInfraCodegenConformDocsOwnership
    from .execute import FlextInfraCodegenConformExecute
    from .existing_plan import FlextInfraCodegenConformExistingPlan
    from .file_plans import FlextInfraCodegenConformFilePlans
    from .gitignore import FlextInfraCodegenConformGitignore
    from .misc import FlextInfraCodegenConformMisc
    from .plan import FlextInfraCodegenConformPlan
    from .pyproject_policy import FlextInfraCodegenConformPyprojectPolicy
    from .scaffold_plan import FlextInfraCodegenConformScaffoldPlan
__all__: tuple[str, ...] = (
    "FlextInfraCodegenConformArtifactRender", "FlextInfraCodegenConformBase", "FlextInfraCodegenConformBeadsRoutes", "FlextInfraCodegenConformBootstrap",
    "FlextInfraCodegenConformContextRender", "FlextInfraCodegenConformDocsOwnership", "FlextInfraCodegenConformExecute", "FlextInfraCodegenConformExistingPlan",
    "FlextInfraCodegenConformFilePlans", "FlextInfraCodegenConformGitignore", "FlextInfraCodegenConformMisc", "FlextInfraCodegenConformPlan",
    "FlextInfraCodegenConformPyprojectPolicy", "FlextInfraCodegenConformRequestFields", "FlextInfraCodegenConformScaffoldPlan",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._request_fields": ("FlextInfraCodegenConformRequestFields",),
            ".artifact_render": ("FlextInfraCodegenConformArtifactRender",),
            ".base": ("FlextInfraCodegenConformBase",),
            ".beads_routes": ("FlextInfraCodegenConformBeadsRoutes",),
            ".bootstrap": ("FlextInfraCodegenConformBootstrap",),
            ".context_render": ("FlextInfraCodegenConformContextRender",),
            ".docs_ownership": ("FlextInfraCodegenConformDocsOwnership",),
            ".execute": ("FlextInfraCodegenConformExecute",),
            ".existing_plan": ("FlextInfraCodegenConformExistingPlan",),
            ".file_plans": ("FlextInfraCodegenConformFilePlans",),
            ".gitignore": ("FlextInfraCodegenConformGitignore",),
            ".misc": ("FlextInfraCodegenConformMisc",),
            ".plan": ("FlextInfraCodegenConformPlan",),
            ".pyproject_policy": ("FlextInfraCodegenConformPyprojectPolicy",),
            ".scaffold_plan": ("FlextInfraCodegenConformScaffoldPlan",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
