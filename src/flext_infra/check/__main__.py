"""CLI entry point for check module."""

from __future__ import annotations

import sys

from flext_infra import u
from flext_infra.check.workspace_check import run_cli


class FlextInfraCheckCommand:
    @staticmethod
    def run(argv: list[str] | None = None) -> int:
        _ = argv
        return run_cli()


def main() -> int:
    """Execute the check CLI and return exit code."""
    return u.Infra.run_cli(FlextInfraCheckCommand.run)


if __name__ == "__main__":
    sys.exit(main())
