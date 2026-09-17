"""Codegen conformance facade: joins the mixin modules via MRO."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_core import s

from ... import m
from .._conform_gitignore import FlextInfraCodegenConformGitignoreMixin
from .bootstrap import FlextInfraCodegenConformBootstrap
from .execute import FlextInfraCodegenConformExecute
from .misc import FlextInfraCodegenConformMisc
from .plan import FlextInfraCodegenConformPlan
from .render import FlextInfraCodegenConformRender


class FlextInfraCodegenConform(
    FlextInfraCodegenConformGitignoreMixin,
    FlextInfraCodegenConformBootstrap,
    FlextInfraCodegenConformMisc,
    FlextInfraCodegenConformRender,
    FlextInfraCodegenConformPlan,
    FlextInfraCodegenConformExecute,
    s[m.Infra.CodegenResult],
):
    """Plan every selected output, then atomically write only a clean plan."""

    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    repository_root: Annotated[
        Path,
        m.Field(default=Path(), exclude=True, description="Conform repository root"),
    ] = Path()
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated scaffold specification included in the atomic plan",
        ),
    ] = None


__all__: list[str] = ["FlextInfraCodegenConform"]
