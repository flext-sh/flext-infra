"""MRO facade for the codegen model namespace.

Models for codegen census, scaffold, and auto-fix pipelines, composed from the
private ``_codegen`` domain partials and the render/toolchain siblings.
"""

from __future__ import annotations

from . import FlextInfraModelsCodegenRender
from ._codegen.base import (
    FlextInfraModelsCodegenCensus,
    FlextInfraModelsCodegenJournal,
    FlextInfraModelsCodegenPolicy,
    FlextInfraModelsCodegenResults,
    FlextInfraModelsCodegenSession,
)
from .codegen_toolchain import FlextInfraModelsCodegenToolchain


class FlextInfraModelsCodegen(
    FlextInfraModelsCodegenRender,
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsCodegenJournal,
    FlextInfraModelsCodegenSession,
    FlextInfraModelsCodegenCensus,
    FlextInfraModelsCodegenPolicy,
    FlextInfraModelsCodegenResults,
):
    """Models for codegen census, scaffold, and auto-fix pipelines."""


__all__: list[str] = ["FlextInfraModelsCodegen"]
