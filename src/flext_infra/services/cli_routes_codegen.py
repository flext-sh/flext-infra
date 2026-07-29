"""Command-selected codegen, check, basemk, and dependency CLI routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import p, t


class CodegenRoutes:
    """Load only the implementation selected by the public group and command."""

    @staticmethod
    def load_generate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected basemk generator route."""
        from flext_infra import m
        from flext_infra.basemk.generator import FlextInfraBaseMkGenerator

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraBaseMkGenerator,
                handler=lambda params: params.execute().map(
                    lambda content: True if params.output is not None else content
                ),
                success_message="base.mk generation complete",
            ),
        )

    @staticmethod
    def load_run(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected workspace-check route."""
        from flext_infra import m
        from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=m.Infra.RunCommand,
                handler=lambda params: FlextInfraWorkspaceChecker.execute_payload(
                    params
                ).map(CliRouteBase.as_route_value),
            ),
        )

    @staticmethod
    def load_fix_pyrefly_settings(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected Pyrefly-settings repair route."""
        from flext_infra import m
        from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=m.Infra.FixPyreflyConfigCommand,
                handler=lambda params: FlextInfraConfigFixer.execute_payload(
                    params
                ).map(CliRouteBase.as_route_value),
            ),
        )

    @staticmethod
    def load_fix_enforcement(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected enforcement repair route."""
        from flext_infra import m
        from flext_infra.fixers.orchestrator import (
            FlextInfraEnforcementFixerOrchestrator,
        )
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=m.Infra.FixEnforcementCommand,
                handler=lambda params: (
                    FlextInfraEnforcementFixerOrchestrator.execute_payload(params).map(
                        CliRouteBase.as_route_value
                    )
                ),
            ),
        )

    @staticmethod
    def load_conform(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected conformance route."""
        from flext_infra import m
        from flext_infra.codegen.conform import FlextInfraCodegenConform

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=m.Infra.CodegenConformRequest,
                handler=FlextInfraCodegenConform.execute_request,
                success_message="project conformance complete",
            ),
        )

    @staticmethod
    def load_new(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected project creation route."""
        from flext_infra import m
        from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenProjectNew,
                handler=FlextInfraCodegenProjectNew.execute_command,
                success_message="project created",
            ),
        )

    @staticmethod
    def load_init(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected lazy-init route."""
        from flext_infra import m
        from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenLazyInit,
                handler=FlextInfraCodegenLazyInit.execute_command,
                success_message="init complete",
            ),
        )

    @staticmethod
    def load_census(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected codegen census route."""
        from flext_infra import m
        from flext_infra.codegen.census import FlextInfraCodegenCensus

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenCensus,
                handler=FlextInfraCodegenCensus.execute_command,
            ),
        )

    @staticmethod
    def load_scaffold(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected scaffold route."""
        from flext_infra import m
        from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenScaffolder,
                handler=FlextInfraCodegenScaffolder.execute_command,
            ),
        )

    @staticmethod
    def load_auto_fix(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected auto-fix route."""
        from flext_infra import m
        from flext_infra.codegen.fixer import FlextInfraCodegenFixer
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenFixer,
                handler=lambda params: FlextInfraCodegenFixer.execute_command(
                    params
                ).map(CliRouteBase.as_route_value),
            ),
        )

    @staticmethod
    def load_py_typed(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected py.typed route."""
        from flext_infra import m
        from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenPyTyped,
                handler=FlextInfraCodegenPyTyped.execute_command,
                success_message="py-typed markers updated",
            ),
        )

    @staticmethod
    def load_pipeline(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected pipeline route."""
        from flext_infra import m
        from flext_infra.codegen.pipeline import FlextInfraCodegenPipeline
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenPipeline,
                handler=lambda params: FlextInfraCodegenPipeline.execute_command(
                    params
                ).map(CliRouteBase.as_route_value),
            ),
        )

    @staticmethod
    def load_constants_quality_gate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected constants quality-gate route."""
        from flext_infra import m
        from flext_infra.codegen.constants_quality_gate import (
            FlextInfraCodegenQualityGate,
        )

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenQualityGate,
                handler=FlextInfraCodegenQualityGate.execute_command,
                success_message="constants quality gate passed",
            ),
        )

    @staticmethod
    def load_consolidate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected consolidator route."""
        from flext_infra import m
        from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenConsolidator,
                handler=FlextInfraCodegenConsolidator.execute_command,
            ),
        )

    @staticmethod
    def load_version_file(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected version-file route."""
        from flext_infra import m
        from flext_infra.codegen.version_file import FlextInfraCodegenVersionFile

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraCodegenVersionFile,
                handler=FlextInfraCodegenVersionFile.execute_command,
                success_message="version-file generation complete",
            ),
        )

    @staticmethod
    def load_detect(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected dependency detector route."""
        from flext_infra import m
        from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraRuntimeDevDependencyDetector,
                handler=lambda params: (
                    FlextInfraRuntimeDevDependencyDetector.execute_command(params).map(
                        CliRouteBase.as_route_value
                    )
                ),
            ),
        )

    @staticmethod
    def load_extra_paths(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected dependency-path route."""
        from flext_infra import m
        from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraExtraPathsManager,
                handler=lambda params: FlextInfraExtraPathsManager.execute_command(
                    params
                ).map(CliRouteBase.as_route_value),
            ),
        )

    @staticmethod
    def load_modernize(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected dependency-modernization route."""
        from flext_infra import m
        from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
        from flext_infra.services.cli_route_base import CliRouteBase

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=FlextInfraPyprojectModernizer,
                handler=lambda params: FlextInfraPyprojectModernizer.execute_command(
                    params
                ).map(CliRouteBase.as_route_value),
            ),
        )


__all__: list[str] = ["CodegenRoutes"]
