"""CLI registration for the docs domain."""

from __future__ import annotations

from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_infra.typings import t


class FlextInfraCliDocs(FlextInfraCliGroupBase):
    """Owns docs CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="audit",
            help_text="Audit documentation for broken links and forbidden terms",
            model_cls=FlextInfraDocAuditor,
            handler=FlextInfraDocAuditor.execute_command,
            success_message="Audit completed successfully",
        ),
        FlextInfraCliGroupBase.route(
            name="fix",
            help_text="Fix documentation issues",
            model_cls=FlextInfraDocFixer,
            handler=FlextInfraDocFixer.execute_command,
            success_message="Fix completed successfully",
        ),
        FlextInfraCliGroupBase.route(
            name="build",
            help_text="Build MkDocs sites",
            model_cls=FlextInfraDocBuilder,
            handler=FlextInfraDocBuilder.execute_command,
            success_message="Build completed successfully",
        ),
        FlextInfraCliGroupBase.route(
            name="generate",
            help_text="Generate project docs",
            model_cls=FlextInfraDocGenerator,
            handler=FlextInfraDocGenerator.execute_command,
            success_message="Generate completed successfully",
        ),
        FlextInfraCliGroupBase.route(
            name="validate",
            help_text="Validate documentation",
            model_cls=FlextInfraDocValidator,
            handler=FlextInfraDocValidator.execute_command,
            success_message="Validate completed successfully",
        ),
    )

    def register_docs(self, app: t.Cli.CliApp) -> None:
        """Register docs routes."""
        FlextInfraCliDocs.register_routes(app)


__all__: list[str] = ["FlextInfraCliDocs"]
