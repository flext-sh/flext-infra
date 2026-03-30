"""FlextInfraCli — MRO-composed CLI facade for all flext-infra commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_cli import cli
from flext_core import FlextRuntime, r

from flext_infra import t
from flext_infra.basemk.cli import FlextInfraCliBasemk
from flext_infra.codegen.cli import FlextInfraCliCodegen
from flext_infra.docs.cli import FlextInfraCliDocs
from flext_infra.github.cli import FlextInfraCliGithub
from flext_infra.refactor.cli import FlextInfraCliRefactor
from flext_infra.release.cli import FlextInfraCliRelease
from flext_infra.validate.cli import FlextInfraCliValidate
from flext_infra.workspace.cli import FlextInfraCliWorkspace
from flext_infra.workspace.maintenance.cli import FlextInfraCliMaintenance

if TYPE_CHECKING:
    import typer


class FlextInfraCli(
    FlextInfraCliBasemk,
    FlextInfraCliCodegen,
    FlextInfraCliDocs,
    FlextInfraCliGithub,
    FlextInfraCliMaintenance,
    FlextInfraCliRefactor,
    FlextInfraCliRelease,
    FlextInfraCliValidate,
    FlextInfraCliWorkspace,
):
    """MRO-composed CLI — each mixin registers its group's commands."""

    app_name: ClassVar[str] = "flext-infra"
    app_help: ClassVar[str] = "FLEXT Infrastructure Tooling"

    def __init__(self) -> None:
        """Initialize CLI app and register all group commands via MRO mixins."""
        FlextRuntime.ensure_structlog_configured()
        self._app: typer.Typer = cli.create_app_with_common_params(
            name=self.app_name,
            help_text=self.app_help,
        )
        self._register_all(self._app)

    def _register_all(self, app: typer.Typer) -> None:
        """Register all group commands on the app."""
        self.register_basemk(app)
        self.register_codegen(app)
        self.register_docs(app)
        self.register_github(app)
        self.register_maintenance(app)
        self.register_refactor(app)
        self.register_validate(app)
        self.register_workspace(app)
        # Release uses handler injection — import here to avoid circular imports
        from flext_infra.release.__main__ import _handle_run  # noqa: PLC0415

        self.register_release(app, handler=_handle_run)

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name=self.app_name, args=args)
