"""Codegen conformance base: joins every responsibility family via MRO."""

from __future__ import annotations

from typing import Annotated

from ... import m, s
from .artifact_render import FlextInfraCodegenConformArtifactRender
from .beads_routes import FlextInfraCodegenConformBeadsRoutes
from .bootstrap import FlextInfraCodegenConformBootstrap
from .context_render import FlextInfraCodegenConformContextRender
from .docs_ownership import FlextInfraCodegenConformDocsOwnership
from .execute import FlextInfraCodegenConformExecute
from .existing_plan import FlextInfraCodegenConformExistingPlan
from .file_plans import FlextInfraCodegenConformFilePlans
from .gitignore import FlextInfraCodegenConformGitignore
from .plan import FlextInfraCodegenConformPlan
from .pyproject_policy import FlextInfraCodegenConformPyprojectPolicy
from .scaffold_plan import FlextInfraCodegenConformScaffoldPlan


class FlextInfraCodegenConformBase(
    FlextInfraCodegenConformExecute,
    FlextInfraCodegenConformPlan,
    FlextInfraCodegenConformScaffoldPlan,
    FlextInfraCodegenConformExistingPlan,
    FlextInfraCodegenConformArtifactRender,
    FlextInfraCodegenConformContextRender,
    FlextInfraCodegenConformBeadsRoutes,
    FlextInfraCodegenConformDocsOwnership,
    FlextInfraCodegenConformFilePlans,
    FlextInfraCodegenConformPyprojectPolicy,
    FlextInfraCodegenConformGitignore,
    FlextInfraCodegenConformBootstrap,
    s[m.Infra.CodegenResult],
):
    """Plan every selected output, then atomically write only a clean plan."""

    # This is the only
    # orchestrator for Make/toolchain/source conformance. Rendering stays in
    # flext-cli; Git-source TOML policy and attached detection are composed from
    # their separately owned u.Infra/workspace services.
    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated scaffold specification included in the atomic plan",
        ),
    ] = None


__all__: list[str] = ["FlextInfraCodegenConformBase"]
