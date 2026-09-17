"""Codegen conformance facade: joins the mixin modules via MRO."""

from __future__ import annotations

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


__all__: list[str] = ["FlextInfraCodegenConform"]
