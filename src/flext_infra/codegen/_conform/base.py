"""Codegen conformance facade: joins the mixin modules via MRO."""

from __future__ import annotations

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
