"""CLI entry point for maintenance."""

from __future__ import annotations

import sys

from flext_infra import t


def main(argv: t.StrSequence | None = None) -> int:
    """Run maintenance CLI.

    Invokes the Typer app in standalone mode so that usage errors
    (e.g. unknown flags) propagate as ``SystemExit(2)`` to the caller.
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    from flext_infra.workspace.maintenance.cli import FlextInfraCliMaintenance

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="maintenance",
        help_text="Enforce Python version constraints via pyproject.toml",
    )
    mixin = FlextInfraCliMaintenance()
    mixin.register_maintenance(app)
    cli_args = list(argv) if argv is not None else sys.argv[1:]
    app(cli_args, standalone_mode=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
