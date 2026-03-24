"""CLI entry point for check module."""

from __future__ import annotations

import sys

from flext_infra import run_cli, t, u


class FlextInfraCheckCommand:
    """CLI entry point for workspace check operations."""

    @staticmethod
    def run(argv: t.StrSequence | None = None) -> int:
        """Execute check CLI."""
        _ = argv
        return run_cli()


def main() -> int:
    """Execute the check CLI and return exit code."""
    return u.Infra.run_cli(FlextInfraCheckCommand.run)


if __name__ == "__main__":
    sys.exit(main())
