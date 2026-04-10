"""CLI registration and compatibility entry points for ``flext-infra check``."""

from __future__ import annotations

from collections.abc import Sequence

from flext_cli import cli as cli_service, m as cli_models
from flext_infra import (
    FlextInfraModelsCheck,
    FlextInfraServiceCheckMixin,
    FlextInfraUtilitiesCliDispatch,
    c,
    t,
)


class FlextInfraCliCheck(FlextInfraServiceCheckMixin):
    """Check CLI group registered on the canonical flext-infra Typer app."""

    def register_check(self, app: t.Cli.CliApp) -> None:
        """Register check commands on the canonical Typer application."""
        cli_service.register_result_routes(
            app,
            [
                cli_models.Cli.ResultCommandRoute(
                    name=c.Infra.Verbs.RUN,
                    help_text="Run quality gates",
                    model_cls=FlextInfraModelsCheck.RunCommand,
                    handler=self.run_workspace_checks,
                    failure_message="check failed",
                ),
                cli_models.Cli.ResultCommandRoute(
                    name="fix-pyrefly-config",
                    help_text="Repair [tool.pyrefly] blocks",
                    model_cls=FlextInfraModelsCheck.FixPyreflyConfigCommand,
                    handler=self.fix_pyrefly_config,
                    failure_message="pyrefly config fix failed",
                ),
            ],
        )


class FlextInfraWorkspaceCheckerCli:
    """Compatibility helpers routed through the canonical check CLI."""

    @staticmethod
    def run_cli(argv: Sequence[str] | None = None) -> int:
        """Run the canonical ``check`` group."""
        return FlextInfraUtilitiesCliDispatch.run_group(
            c.Infra.Verbs.CHECK,
            argv,
        )

    @staticmethod
    def main(argv: Sequence[str] | None = None) -> int:
        """Legacy entrypoint routed through ``flext-infra check run``."""
        return FlextInfraUtilitiesCliDispatch.run_command(
            c.Infra.Verbs.CHECK,
            c.Infra.Verbs.RUN,
            argv,
        )


__all__ = ["FlextInfraCliCheck", "FlextInfraWorkspaceCheckerCli"]
