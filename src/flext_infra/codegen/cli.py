"""CLI mixin for codegen commands."""

from __future__ import annotations

from flext_cli import cli
from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPipeline,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    FlextInfraConstantsCodegenQualityGate,
    m,
    t,
)


class FlextInfraCliCodegen:
    """Codegen CLI group — composed into FlextInfraCli via MRO."""

    def register_codegen(self, app: t.Cli.CliApp) -> None:
        """Register codegen commands on the given Typer app."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="lazy-init",
                    help_text="Generate/refresh PEP 562 lazy-import __init__.py files",
                    model_cls=FlextInfraCodegenLazyInit,
                    handler=FlextInfraCodegenLazyInit.execute_command,
                    failure_message="lazy-init failed",
                    success_message="lazy-init complete",
                ),
                m.Cli.ResultCommandRoute(
                    name="census",
                    help_text="Count namespace violations across workspace projects",
                    model_cls=FlextInfraCodegenCensus,
                    handler=FlextInfraCodegenCensus.execute_command,
                    failure_message="census failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="scaffold",
                    help_text="Generate missing base modules in src/ and tests/",
                    model_cls=FlextInfraCodegenScaffolder,
                    handler=FlextInfraCodegenScaffolder.execute_command,
                    failure_message="scaffold failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="auto-fix",
                    help_text="Auto-fix namespace violations (move Finals/TypeVars)",
                    model_cls=FlextInfraCodegenFixer,
                    handler=FlextInfraCodegenFixer.execute_command,
                    failure_message="auto-fix failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="py-typed",
                    help_text="Create/remove PEP 561 py.typed markers",
                    model_cls=FlextInfraCodegenPyTyped,
                    handler=FlextInfraCodegenPyTyped.execute_command,
                    failure_message="py-typed failed",
                    success_message="py-typed markers updated",
                ),
                m.Cli.ResultCommandRoute(
                    name="pipeline",
                    help_text="Run full codegen pipeline",
                    model_cls=FlextInfraCodegenPipeline,
                    handler=FlextInfraCodegenPipeline.execute_command,
                    failure_message="pipeline failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="constants-quality-gate",
                    help_text="Run constants migration quality gate",
                    model_cls=FlextInfraConstantsCodegenQualityGate,
                    handler=FlextInfraConstantsCodegenQualityGate.execute_command,
                    failure_message="constants quality gate failed",
                    success_message="constants quality gate passed",
                ),
                m.Cli.ResultCommandRoute(
                    name="consolidate",
                    help_text="Consolidate inline constants into c.Infra.* references",
                    model_cls=FlextInfraCodegenConsolidator,
                    handler=FlextInfraCodegenConsolidator.execute_command,
                    failure_message="consolidate failed",
                ),
            ],
        )


__all__ = ["FlextInfraCliCodegen"]
