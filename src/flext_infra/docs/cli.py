"""CLI mixin for documentation commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from flext_infra import FlextInfra


class FlextInfraCliDocs:
    """Docs CLI group — composed into FlextInfraCli via MRO."""

    def register_docs(self: FlextInfra, app: t.Cli.CliApp) -> None:
        """Register documentation commands on the given Typer app."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="audit",
                    help_text="Audit documentation for broken links and forbidden terms",
                    model_cls=FlextInfraDocAuditor,
                    handler=self.audit_docs,
                    failure_message="Audit failed",
                    success_message="Audit completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="fix",
                    help_text="Fix documentation issues",
                    model_cls=FlextInfraDocFixer,
                    handler=self.fix_docs,
                    failure_message="Fix failed",
                    success_message="Fix completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="build",
                    help_text="Build MkDocs sites",
                    model_cls=FlextInfraDocBuilder,
                    handler=self.build_docs,
                    failure_message="Build failed",
                    success_message="Build completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="generate",
                    help_text="Generate project docs",
                    model_cls=FlextInfraDocGenerator,
                    handler=self.generate_docs,
                    failure_message="Generate failed",
                    success_message="Generate completed successfully",
                ),
                m.Cli.ResultCommandRoute(
                    name="validate",
                    help_text="Validate documentation",
                    model_cls=FlextInfraDocValidator,
                    handler=self.validate_docs,
                    failure_message="Validate failed",
                    success_message="Validate completed successfully",
                ),
            ],
        )


__all__ = ["FlextInfraCliDocs"]
