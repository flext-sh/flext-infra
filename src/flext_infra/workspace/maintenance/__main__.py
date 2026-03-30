"""CLI entry point for maintenance services.

Usage:
    python -m flext_infra maintenance run [--check] [--verbose]

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys

from flext_cli import cli
from flext_core import FlextRuntime, r

from flext_infra import FlextInfraPythonVersionEnforcer, m, t

# ── Router ───────────────────────────────────────────────────


class FlextInfraMaintenanceCli:
    """Declarative CLI router for workspace maintenance operations."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="maintenance",
            help_text="Enforce Python version constraints via pyproject.toml",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="maintenance", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="run",
                help_text="Execute maintenance operations",
                model_cls=m.Infra.MaintenanceRunInput,
                handler=self._handle_run,
                success_message="Maintenance completed successfully",
                failure_message="Maintenance failed",
            ),
        )

    @staticmethod
    def _handle_run(params: m.Infra.MaintenanceRunInput) -> r[int]:
        service = FlextInfraPythonVersionEnforcer()
        return service.execute(check_only=params.check, verbose=params.verbose)


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Run maintenance service CLI."""
    FlextRuntime.ensure_structlog_configured()
    instance = FlextInfraMaintenanceCli()
    result = instance.run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
