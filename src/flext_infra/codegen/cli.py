"""CLI mixin for codegen commands."""

from __future__ import annotations

from flext_cli import cli
from flext_infra import m, t
from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.codegen.constants_quality_gate import (
    FlextInfraConstantsCodegenQualityGate,
)
from flext_infra.codegen.fixer import FlextInfraCodegenFixer
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
from flext_infra.codegen.pyproject_keys import FlextInfraCodegenPyprojectKeys
from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile
from flext_infra.services.consolidator import FlextInfraCodegenConsolidator
from flext_infra.services.pipeline import FlextInfraCodegenPipeline


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
                m.Cli.ResultCommandRoute(
                    name="pyproject-keys",
                    help_text="Generate [tool.flext.*] tables in pyproject.toml",
                    model_cls=FlextInfraCodegenPyprojectKeys,
                    handler=FlextInfraCodegenPyprojectKeys.execute_command,
                    failure_message="pyproject-keys generation failed",
                    success_message="pyproject-keys generation complete",
                ),
                m.Cli.ResultCommandRoute(
                    name="version-file",
                    help_text="Generate __version__.py from project-metadata SSOT",
                    model_cls=FlextInfraCodegenVersionFile,
                    handler=FlextInfraCodegenVersionFile.execute_command,
                    failure_message="version-file generation failed",
                    success_message="version-file generation complete",
                ),
            ],
        )


__all__: list[str] = ["FlextInfraCliCodegen"]
