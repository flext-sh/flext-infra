"""CLI mixin for refactor commands."""

from __future__ import annotations

from flext_cli import cli as cli_service
from flext_infra import FlextInfraServiceRefactorMixin, m, t


class FlextInfraCliRefactor(FlextInfraServiceRefactorMixin):
    """Refactor CLI group — composed into FlextInfraCli via MRO."""

    def register_refactor(self, app: t.Cli.CliApp) -> None:
        """Register refactor commands on the given Typer app."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="migrate-mro",
                    help_text="Migrate loose declarations into MRO facade classes",
                    model_cls=m.Infra.RefactorMigrateMroInput,
                    handler=self.migrate_mro,
                    failure_message="MRO migration failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="namespace-enforce",
                    help_text="Scan workspace for namespace governance violations",
                    model_cls=m.Infra.RefactorNamespaceEnforceInput,
                    handler=self.enforce_namespace,
                    failure_message="Namespace enforcement failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="census",
                    help_text="Run rope-oriented census of MRO family method usage",
                    model_cls=m.Infra.RefactorCensusInput,
                    handler=self.run_refactor_census,
                    failure_message="Census failed",
                ),
            ],
        )


__all__ = ["FlextInfraCliRefactor"]
