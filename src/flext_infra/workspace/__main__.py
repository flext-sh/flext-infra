"""CLI entry point for workspace."""

from __future__ import annotations

import sys

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

_SUBCOMMANDS: frozenset[str] = frozenset({
    "detect",
    "sync",
    "orchestrate",
    "migrate",
})


def _normalize_argv(raw: list[str]) -> list[str]:
    """Reorder args so the subcommand comes first (Click requirement).

    Handles invocations like ``--workspace . --dry-run migrate`` by moving
    the subcommand name to the front: ``migrate --workspace . --dry-run``.
    """
    for idx, arg in enumerate(raw):
        if arg in _SUBCOMMANDS:
            return [arg, *raw[:idx], *raw[idx + 1 :]]
    return raw


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
        raw = list(sys.argv[1:])
        if raw and raw[0] == "workspace":
            raw = raw[1:]
        cli_args: list[str] = _normalize_argv(raw)
    else:
        cli_args = _normalize_argv(list(argv))
    result = cli.execute_app(app, prog_name="workspace", args=cli_args)
    if result.is_failure:
        error_msg = result.error or ""
        if _is_usage_error(error_msg):
            return 2
    return 0 if result.is_success else 1


_USAGE_ERROR_MARKERS: tuple[str, ...] = (
    "No such option",
    "No such command",
    "Missing option",
    "Missing argument",
    "Got unexpected extra argument",
    "exited with code 2",
)


def _is_usage_error(msg: str) -> bool:
    """Return True when *msg* looks like a Click/Typer usage error."""
    return any(marker in msg for marker in _USAGE_ERROR_MARKERS)


if __name__ == "__main__":
    sys.exit(main())
