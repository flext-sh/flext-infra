"""Codegen conformance base: the final class of the linear responsibility chain."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_core import s

from ... import m
from .._conform_gitignore import FlextInfraCodegenConformGitignoreMixin
from .bootstrap import FlextInfraCodegenConformBootstrap
from .execute import FlextInfraCodegenConformExecute


class FlextInfraCodegenConformBase(FlextInfraCodegenConformExecute):
    """Plan every selected output, then atomically write only a clean plan.

    The chain is linear in dependency order, so every responsibility statically
    inherits what it calls: bootstrap (service root, request state) <- gitignore
    <- docs ownership <- beads routes <- file plans <- pyproject policy <-
    context render <- artifact render <- existing plan <- scaffold plan <- plan
    <- execute.
    """

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


__all__: list[str] = ["FlextInfraCodegenConformBase"]
