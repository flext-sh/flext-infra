"""CLI registration for the check domain."""

from __future__ import annotations

from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.constants import c
from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer
from flext_infra.models import FlextInfraModelsCheck
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraCliCheck(FlextInfraCliGroupBase):
    """Owns check CLI route declarations."""

    @staticmethod
    def _run_workspace_checks(
        params: FlextInfraModelsCheck.RunCommand,
    ) -> p.Result[bool]:
        checker = FlextInfraWorkspaceChecker(workspace_root=params.workspace_path)
        return checker.run_command(params)

    @staticmethod
    def _fix_pyrefly_config(
        params: FlextInfraModelsCheck.FixPyreflyConfigCommand,
    ) -> p.Result[bool]:
        fixer = FlextInfraConfigFixer(workspace=params.workspace_path)
        return fixer.run_command(params)

    routes = (
        FlextInfraCliGroupBase.route(
            name=c.Infra.VERB_RUN,
            help_text="Run quality gates",
            model_cls=FlextInfraModelsCheck.RunCommand,
            handler=_run_workspace_checks,
        ),
        FlextInfraCliGroupBase.route(
            name="fix-pyrefly-settings",
            help_text="Repair [tool.pyrefly] blocks",
            model_cls=FlextInfraModelsCheck.FixPyreflyConfigCommand,
            handler=_fix_pyrefly_config,
        ),
    )

    def register_check(self, app: t.Cli.CliApp) -> None:
        """Register check routes."""
        FlextInfraCliCheck.register_routes(app)


__all__: list[str] = ["FlextInfraCliCheck"]
