"""Codegen conformance facade: joins the mixin modules via MRO."""

from __future__ import annotations

from typing import Annotated

from ... import m, s
from .._conform_gitignore import FlextInfraCodegenConformGitignoreMixin

from .bootstrap import FlextInfraCodegenConformBootstrap
from .execute import FlextInfraCodegenConformExecute
from .misc import FlextInfraCodegenConformMisc
from .plan import FlextInfraCodegenConformPlan
from .render import FlextInfraCodegenConformRender


class FlextInfraCodegenConform(
    FlextInfraCodegenConformGitignoreMixin,
    s[m.Infra.CodegenResult],
    FlextInfraCodegenConformBootstrap,
    FlextInfraCodegenConformPlan,
    FlextInfraCodegenConformExecute,
    FlextInfraCodegenConformRender,
    FlextInfraCodegenConformMisc,
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


__all__: list[str] = ["FlextInfraCodegenConform"]