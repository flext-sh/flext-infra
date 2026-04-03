"""CLI mixin for codegen commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, u
from flext_infra.codegen._cli_codegen_consolidate import (
    FlextInfraCliCodegenConsolidate,
)
from flext_infra.codegen._cli_codegen_handlers import FlextInfraCliCodegenHandlers

if TYPE_CHECKING:
    import typer

_R = u.Infra.route  # shorthand


def _format_text(value: str) -> str:
    """Format text result for CLI output."""
    return str(value)


class FlextInfraCliCodegen(
    FlextInfraCliCodegenConsolidate,
    FlextInfraCliCodegenHandlers,
):
    """Codegen CLI group — composed into FlextInfraCli via MRO."""

    def register_codegen(self, app: typer.Typer) -> None:
        """Register codegen commands on the given Typer app."""
        u.Infra.register_routes(
            app,
            [
                _R(
                    "lazy-init",
                    "Generate/refresh PEP 562 lazy-import __init__.py files",
                    m.Infra.CodegenLazyInitInput,
                    self._handle_lazy_init,
                    success_msg="lazy-init complete",
                ),
                _R(
                    "census",
                    "Count namespace violations across workspace projects",
                    m.Infra.CodegenCensusInput,
                    self._handle_codegen_census,
                    formatter=_format_text,
                ),
                _R(
                    "deduplicate",
                    "Auto-fix duplicated constants (keep most-used)",
                    m.Infra.CodegenDeduplicateInput,
                    self._handle_deduplicate,
                    formatter=_format_text,
                ),
                _R(
                    "scaffold",
                    "Generate missing base modules in src/ and tests/",
                    m.Infra.CodegenScaffoldInput,
                    self._handle_scaffold,
                    formatter=_format_text,
                ),
                _R(
                    "auto-fix",
                    "Auto-fix namespace violations (move Finals/TypeVars)",
                    m.Infra.CodegenAutoFixInput,
                    self._handle_auto_fix,
                    formatter=_format_text,
                ),
                _R(
                    "py-typed",
                    "Create/remove PEP 561 py.typed markers",
                    m.Infra.CodegenPyTypedInput,
                    self._handle_py_typed,
                    success_msg="py-typed markers updated",
                ),
                _R(
                    "pipeline",
                    "Run full codegen pipeline",
                    m.Infra.CodegenPipelineInput,
                    self._handle_pipeline,
                    formatter=_format_text,
                ),
                _R(
                    "constants-quality-gate",
                    "Run constants migration quality gate",
                    m.Infra.CodegenConstantsQualityGateInput,
                    self._handle_constants_quality_gate,
                    fail_msg="constants quality gate failed",
                    success_msg="constants quality gate passed",
                ),
                _R(
                    "consolidate",
                    "Consolidate inline constants into c.Infra.* references",
                    m.Infra.CodegenConsolidateInput,
                    self._handle_consolidate,
                    formatter=_format_text,
                ),
            ],
        )


__all__ = ["FlextInfraCliCodegen"]
