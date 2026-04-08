"""CLI mixin for refactor commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli as cli_service
from flext_infra import m, t

if TYPE_CHECKING:
    from flext_infra import FlextInfra


class FlextInfraCliRefactor:
    """Refactor CLI group — composed into FlextInfraCli via MRO."""

    def register_refactor(self: FlextInfra, app: t.Cli.CliApp) -> None:
        """Register refactor commands on the given Typer app."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="centralize-pydantic",
                    help_text="Centralize BaseModel/TypedDict/dict-like aliases into _models.py",
                    model_cls=m.Infra.RefactorCentralizeInput,
                    handler=self.centralize_pydantic,
                    failure_message="Pydantic centralization failed",
                ),
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
                    name="migrate-runtime-alias-imports",
                    help_text="Normalize canonical aliases like c/m/p/t/u/r/s to the correct local MRO root import",
                    model_cls=m.Infra.RefactorMigrateRuntimeAliasImportsInput,
                    handler=self.migrate_runtime_alias_imports,
                    failure_message="Runtime alias import migration failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="ultrawork-models",
                    help_text="Run full centralization + MRO + namespace workflow",
                    model_cls=m.Infra.RefactorUltraworkModelsInput,
                    handler=self.ultrawork_models,
                    failure_message="Ultrawork models failed",
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
