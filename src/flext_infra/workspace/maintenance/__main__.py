"""CLI entry point for maintenance services.

Usage:
    python -m flext_infra maintenance [--workspace PATH] [--verbose]

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys

from flext_infra import FlextInfraPythonVersionEnforcer, output, r, u


class FlextInfraWorkspaceMaintenanceCommand:
    @staticmethod
    def run(argv: list[str] | None = None) -> int:
        """Execute maintenance CLI and return service exit code."""
        parser = u.Infra.create_parser(
            prog="maintenance",
            description="Enforce Python version constraints via pyproject.toml",
            include_check=True,
        )
        _ = parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output",
        )
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        service = FlextInfraPythonVersionEnforcer()
        result: r[int] = service.execute(check_only=cli.check, verbose=args.verbose)
        if result.is_success:
            return result.unwrap()
        output.error(result.error or "maintenance failed")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Run maintenance service CLI."""
    return FlextInfraWorkspaceMaintenanceCommand.run(argv)


if __name__ == "__main__":
    sys.exit(u.Infra.run_cli(main))
