"""Command-selected codegen, check, basemk, and dependency CLI routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.cli_catalog import CliCatalog

if TYPE_CHECKING:
    from flext_infra import m


class CodegenRoutes:
    """Load only the implementation selected by the public group and command."""

    @classmethod
    def routes_for(
        cls, group: str, command: str
    ) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Build the one route selected at the lightweight dispatch boundary."""
        from flext_infra import m

        if (group, command) == ("basemk", "generate"):
            from flext_infra.basemk.generator import FlextInfraBaseMkGenerator

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=FlextInfraBaseMkGenerator,
                    handler=lambda params: params.execute().map(
                        lambda content: True if params.output is not None else content
                    ),
                    success_message="base.mk generation complete",
                ),
            )
        if (group, command) == ("check", "run"):
            from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
            from flext_infra.services.cli_route_base import CliRouteBase

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=m.Infra.RunCommand,
                    handler=lambda params: FlextInfraWorkspaceChecker.execute_payload(
                        params
                    ).map(CliRouteBase.as_route_value),
                ),
            )
        if (group, command) == ("check", "fix-pyrefly-settings"):
            from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
            from flext_infra.services.cli_route_base import CliRouteBase

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=m.Infra.FixPyreflyConfigCommand,
                    handler=lambda params: FlextInfraConfigFixer.execute_payload(
                        params
                    ).map(CliRouteBase.as_route_value),
                ),
            )
        if (group, command) == ("check", "fix-enforcement"):
            from flext_infra.fixers.orchestrator import (
                FlextInfraEnforcementFixerOrchestrator,
            )
            from flext_infra.services.cli_route_base import CliRouteBase

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=m.Infra.FixEnforcementCommand,
                    handler=lambda params: (
                        FlextInfraEnforcementFixerOrchestrator.execute_payload(
                            params
                        ).map(CliRouteBase.as_route_value)
                    ),
                ),
            )
        if (group, command) == ("codegen", "conform"):
            from flext_infra.codegen.conform import FlextInfraCodegenConform

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=CliCatalog.description(group, command),
                    model_cls=m.Infra.CodegenConformRequest,
                    handler=FlextInfraCodegenConform.execute_request,
                    success_message="project conformance complete",
                ),
            )

        if group == "codegen":
            if command == "new":
                from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew

                implementation = FlextInfraCodegenProjectNew
                success_message = "project created"
            elif command == "init":
                from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit

                implementation = FlextInfraCodegenLazyInit
                success_message = "init complete"
            elif command == "census":
                from flext_infra.codegen.census import FlextInfraCodegenCensus

                implementation = FlextInfraCodegenCensus
                success_message = None
            elif command == "scaffold":
                from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder

                implementation = FlextInfraCodegenScaffolder
                success_message = None
            elif command == "auto-fix":
                from flext_infra.codegen.fixer import FlextInfraCodegenFixer

                implementation = FlextInfraCodegenFixer
                success_message = None
            elif command == "py-typed":
                from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped

                implementation = FlextInfraCodegenPyTyped
                success_message = "py-typed markers updated"
            elif command == "pipeline":
                from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline

                implementation = FlextInfraCodegenPipeline
                success_message = None
            elif command == "constants-quality-gate":
                from flext_infra.codegen.constants_quality_gate import (
                    FlextInfraCodegenQualityGate,
                )

                implementation = FlextInfraCodegenQualityGate
                success_message = "constants quality gate passed"
            elif command == "consolidate":
                from flext_infra.codegen.consolidator import (
                    FlextInfraCodegenConsolidator,
                )

                implementation = FlextInfraCodegenConsolidator
                success_message = None
            elif command == "version-file":
                from flext_infra.codegen.version_file import (
                    FlextInfraCodegenVersionFile,
                )

                implementation = FlextInfraCodegenVersionFile
                success_message = "version-file generation complete"
            else:
                return ()
        elif group == "deps":
            if command == "detect":
                from flext_infra.deps.detector import (
                    FlextInfraRuntimeDevDependencyDetector,
                )

                implementation = FlextInfraRuntimeDevDependencyDetector
            elif command == "extra-paths":
                from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager

                implementation = FlextInfraExtraPathsManager
            elif command == "modernize":
                from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer

                implementation = FlextInfraPyprojectModernizer
            else:
                return ()
            success_message = None
        else:
            return ()

        return (
            m.Cli.ResultCommandRoute(
                name=command,
                help_text=CliCatalog.description(group, command),
                model_cls=implementation,
                handler=lambda params, mc=implementation: mc.execute_command(params),
                success_message=success_message,
            ),
        )


__all__: list[str] = ["CodegenRoutes"]
