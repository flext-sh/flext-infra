"""CLI mixin for documentation commands."""

from __future__ import annotations

from flext_cli import cli as cli_service
from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    m,
    t,
)


class FlextInfraCliDocs:
    """Docs CLI group — composed into FlextInfraCli via MRO."""

    def register_docs(self, app: t.Cli.CliApp) -> None:
        """Register documentation commands on the given Typer app."""
        auditor = FlextInfraDocAuditor()
        fixer = FlextInfraDocFixer()
        builder = FlextInfraDocBuilder()
        generator = FlextInfraDocGenerator()
        validator = FlextInfraDocValidator()
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="audit",
                    help_text="Audit documentation for broken links and forbidden terms",
                    model_cls=m.Infra.DocsAuditInput,
                    handler=auditor.execute_command,
                    failure_message="Audit failed",
                    success_message="Audit completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="fix",
                    help_text="Fix documentation issues",
                    model_cls=m.Infra.DocsFixInput,
                    handler=fixer.execute_command,
                    failure_message="Fix failed",
                    success_message="Fix completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="build",
                    help_text="Build MkDocs sites",
                    model_cls=m.Infra.DocsBuildInput,
                    handler=builder.execute_command,
                    failure_message="Build failed",
                    success_message="Build completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="generate",
                    help_text="Generate project docs",
                    model_cls=m.Infra.DocsGenerateInput,
                    handler=generator.execute_command,
                    failure_message="Generate failed",
                    success_message="Generate completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="validate",
                    help_text="Validate documentation",
                    model_cls=m.Infra.DocsValidateInput,
                    handler=validator.execute_command,
                    failure_message="Validate failed",
                    success_message="Validate completed successfully",
                ),
            ],
        )


__all__ = ["FlextInfraCliDocs"]
