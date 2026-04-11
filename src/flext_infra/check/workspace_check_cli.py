"""CLI group registration for ``flext-infra check``."""

from __future__ import annotations

from flext_cli import m as cli_models
from flext_cli.api import cli as cli_service
from flext_infra import (
    FlextInfraModelsCheck,
    FlextInfraServiceCheckMixin,
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
                    name=c.Infra.VERB_RUN,
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


__all__ = ["FlextInfraCliCheck"]
