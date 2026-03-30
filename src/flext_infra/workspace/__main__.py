"""CLI entry point for workspace."""

from __future__ import annotations

import sys

import click

from flext_infra import m, t
from flext_infra.workspace.cli import (
    FlextInfraCliWorkspace,
)

# Re-export handlers for test backward compatibility
_handle_detect = FlextInfraCliWorkspace._handle_detect
_handle_sync = FlextInfraCliWorkspace._handle_sync
_handle_orchestrate = FlextInfraCliWorkspace._handle_orchestrate
_handle_migrate = FlextInfraCliWorkspace._handle_migrate

# Module reference for dynamic handler lookup
_THIS_MODULE = sys.modules[__name__]


def main(argv: t.StrSequence | None = None) -> int:
    """Run workspace CLI.

    Invokes the Typer app via execute_app so that usage errors
    are normalized into ``r[bool]`` results.
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="workspace",
        help_text="Workspace management utilities",
    )
    # Register routes using module-level handler lookup so tests can
    # monkeypatch _handle_* on this module and have the change take effect.
    cli.register_result_route(
        app,
        route=m.Cli.ResultCommandRouteModel(
            name="detect",
            help_text="Detect workspace or standalone mode",
            model_cls=m.Infra.WorkspaceDetectInput,
            handler=lambda params: getattr(_THIS_MODULE, "_handle_detect")(params),
            failure_message="detection failed",
        ),
    )
    cli.register_result_route(
        app,
        route=m.Cli.ResultCommandRouteModel(
            name="sync",
            help_text="Sync base.mk to project root",
            model_cls=m.Infra.WorkspaceSyncInput,
            handler=lambda params: getattr(_THIS_MODULE, "_handle_sync")(params),
            failure_message="sync failed",
        ),
    )
    cli.register_result_route(
        app,
        route=m.Cli.ResultCommandRouteModel(
            name="orchestrate",
            help_text="Run make verb across projects",
            model_cls=m.Infra.WorkspaceOrchestrateInput,
            handler=lambda params: getattr(_THIS_MODULE, "_handle_orchestrate")(params),
            failure_message="orchestration failed",
        ),
    )
    cli.register_result_route(
        app,
        route=m.Cli.ResultCommandRouteModel(
            name="migrate",
            help_text="Migrate workspace projects to flext_infra tooling",
            model_cls=m.Infra.WorkspaceMigrateInput,
            handler=lambda params: getattr(_THIS_MODULE, "_handle_migrate")(params),
            failure_message="migration failed",
        ),
    )
    # When argv is None, compute CLI args from sys.argv.
    # The parent dispatcher (flext-infra __main__) rewrites sys.argv as
    # ["flext-infra workspace", ...remaining...], but direct invocation may
    # leave sys.argv as ["flext-infra", "workspace", ...remaining...].
    # Strip the known group name if present at sys.argv[1].
    if argv is None:
        raw = sys.argv[1:]
        if raw and raw[0] == "workspace":
            raw = raw[1:]
        cli_args: t.StrSequence = raw
    else:
        cli_args = argv
    try:
        result = cli.execute_app(app, prog_name="workspace", args=cli_args)
    except click.UsageError:
        return 2
    if result.is_failure:
        error_msg = result.error or ""
        if "exited with code 2" in error_msg:
            return 2
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
