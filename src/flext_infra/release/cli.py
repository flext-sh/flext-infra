"""CLI mixin for release commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli, p

from flext_infra import m

if TYPE_CHECKING:
    import typer


class FlextInfraCliRelease:
    """Release CLI group — composed into FlextInfraCli via MRO."""

    def register_release(
        self,
        app: typer.Typer,
        *,
        handler: p.Cli.ResultCommandHandler[m.Infra.ReleaseRunInput, bool],
    ) -> None:
        """Register release commands on the given Typer app.

        The handler is injected by the caller so that module-level names
        (e.g. ``FlextInfraReleaseOrchestrator``) remain patchable in tests.
        """
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="run",
                help_text="Run release orchestration CLI flow",
                model_cls=m.Infra.ReleaseRunInput,
                handler=handler,
                success_message="Release completed successfully",
                failure_message="Release failed",
            ),
        )
