"""CLI registration for the codegen domain."""

from __future__ import annotations

from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
from flext_infra.codegen.constants_quality_gate import (
    FlextInfraConstantsCodegenQualityGate,
)
from flext_infra.codegen.fixer import FlextInfraCodegenFixer
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline
from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped
from flext_infra.codegen.pyproject_keys import FlextInfraCodegenPyprojectKeys
from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile
from flext_infra.typings import t


class FlextInfraCliCodegen(FlextInfraCliGroupBase):
    """Owns codegen CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="init",
            help_text="Generate/refresh PEP 562 lazy-import __init__.py files",
            model_cls=FlextInfraCodegenLazyInit,
            handler=FlextInfraCodegenLazyInit.execute_command,
            success_message="init complete",
        ),
        FlextInfraCliGroupBase.route(
            name="census",
            help_text="Count namespace violations across workspace projects",
            model_cls=FlextInfraCodegenCensus,
            handler=FlextInfraCodegenCensus.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="scaffold",
            help_text="Generate missing base modules in src/ and tests/",
            model_cls=FlextInfraCodegenScaffolder,
            handler=FlextInfraCodegenScaffolder.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="auto-fix",
            help_text="Auto-fix namespace violations (move Finals/TypeVars)",
            model_cls=FlextInfraCodegenFixer,
            handler=FlextInfraCodegenFixer.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="py-typed",
            help_text="Create/remove PEP 561 py.typed markers",
            model_cls=FlextInfraCodegenPyTyped,
            handler=FlextInfraCodegenPyTyped.execute_command,
            success_message="py-typed markers updated",
        ),
        FlextInfraCliGroupBase.route(
            name="pipeline",
            help_text="Run full codegen pipeline",
            model_cls=FlextInfraCodegenPipeline,
            handler=FlextInfraCodegenPipeline.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="constants-quality-gate",
            help_text="Run constants migration quality gate",
            model_cls=FlextInfraConstantsCodegenQualityGate,
            handler=FlextInfraConstantsCodegenQualityGate.execute_command,
            success_message="constants quality gate passed",
        ),
        FlextInfraCliGroupBase.route(
            name="consolidate",
            help_text="Consolidate inline constants into c.Infra.* references",
            model_cls=FlextInfraCodegenConsolidator,
            handler=FlextInfraCodegenConsolidator.execute_command,
        ),
        FlextInfraCliGroupBase.route(
            name="pyproject-keys",
            help_text="Generate [tool.flext.*] tables in pyproject.toml",
            model_cls=FlextInfraCodegenPyprojectKeys,
            handler=FlextInfraCodegenPyprojectKeys.execute_command,
            success_message="pyproject-keys generation complete",
        ),
        FlextInfraCliGroupBase.route(
            name="version-file",
            help_text="Generate __version__.py from project-metadata SSOT",
            model_cls=FlextInfraCodegenVersionFile,
            handler=FlextInfraCodegenVersionFile.execute_command,
            success_message="version-file generation complete",
        ),
    )

    def register_codegen(self, app: t.Cli.CliApp) -> None:
        """Register codegen routes."""
        FlextInfraCliCodegen.register_routes(app)


__all__: list[str] = ["FlextInfraCliCodegen"]
