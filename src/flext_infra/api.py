"""Public API facade for flext-infra."""

from __future__ import annotations

from typing import ClassVar, Self, override

from flext_cli import cli
from flext_infra import (
    FlextInfraCliBasemk,
    FlextInfraCliCheck,
    FlextInfraCliCodegen,
    FlextInfraCliDeps,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    FlextInfraServiceBase,
    FlextInfraServiceBasemkMixin,
    FlextInfraServiceCheckMixin,
    FlextInfraServiceDepsMixin,
    FlextInfraServiceGithubMixin,
    FlextInfraServiceRefactorMixin,
    FlextInfraServiceReleaseMixin,
    FlextInfraServiceRopeMixin,
    FlextInfraServiceValidateMixin,
    FlextInfraServiceWorkspaceMixin,
    m,
    p,
    r,
    t,
)


class FlextInfra(
    FlextInfraCliBasemk,
    FlextInfraCliCheck,
    FlextInfraCliCodegen,
    FlextInfraCliDeps,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
    FlextInfraServiceBasemkMixin,
    FlextInfraServiceCheckMixin,
    FlextInfraServiceDepsMixin,
    FlextInfraServiceGithubMixin,
    FlextInfraServiceRopeMixin,
    FlextInfraServiceRefactorMixin,
    FlextInfraServiceReleaseMixin,
    FlextInfraServiceValidateMixin,
    FlextInfraServiceWorkspaceMixin,
    FlextInfraServiceBase[t.MutableRecursiveContainerMapping],
):
    """Thin public MRO facade over infra services and CLI groups."""

    app_name: ClassVar[str] = "flext-infra"
    _instance: ClassVar[Self | None] = None

    @classmethod
    def get_instance(cls) -> Self:
        """Return the shared infra facade instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @override
    def execute(self) -> p.Result[t.MutableRecursiveContainerMapping]:
        """Execute a lightweight facade health report."""
        report: t.MutableRecursiveContainerMapping = {
            "service": "flext-infra",
            "status": "ok",
            "workspace_root": str(self.workspace_root),
            "apply_changes": self.apply_changes,
        }
        return r[t.MutableRecursiveContainerMapping].ok(report)

    def register_docs(self, app: t.Cli.CliApp) -> None:
        """Register docs commands directly on the concrete service classes."""
        cli.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="audit",
                    help_text="Audit documentation for broken links and forbidden terms",
                    model_cls=FlextInfraDocAuditor,
                    handler=FlextInfraDocAuditor.execute_command,
                    failure_message="Audit failed",
                    success_message="Audit completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="fix",
                    help_text="Fix documentation issues",
                    model_cls=FlextInfraDocFixer,
                    handler=FlextInfraDocFixer.execute_command,
                    failure_message="Fix failed",
                    success_message="Fix completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="build",
                    help_text="Build MkDocs sites",
                    model_cls=FlextInfraDocBuilder,
                    handler=FlextInfraDocBuilder.execute_command,
                    failure_message="Build failed",
                    success_message="Build completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="generate",
                    help_text="Generate project docs",
                    model_cls=FlextInfraDocGenerator,
                    handler=FlextInfraDocGenerator.execute_command,
                    failure_message="Generate failed",
                    success_message="Generate completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="validate",
                    help_text="Validate documentation",
                    model_cls=FlextInfraDocValidator,
                    handler=FlextInfraDocValidator.execute_command,
                    failure_message="Validate failed",
                    success_message="Validate completed successfully",
                ),
            ],
        )


infra = FlextInfra.get_instance()


__all__: list[str] = ["FlextInfra", "infra"]
