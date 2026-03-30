"""CLI entry point for refactor."""

from __future__ import annotations

import sys

from flext_cli import cli
from flext_core import FlextRuntime

from flext_infra import FlextInfraCliRefactor, t


def main(argv: t.StrSequence | None = None) -> int:
    """Run refactor CLI.

    Uses ``cli.execute_app`` to normalize Typer exit behavior into ``r[bool]``
    so callers get an integer exit code (0 = success, 1 = failure, 2 = usage).
    """
    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="refactor",
        help_text="Refactor and modernization tools for flext workspace",
    )
    mixin = FlextInfraCliRefactor()
    mixin.register_refactor(app)
    result = cli.execute_app(app, prog_name="refactor", args=argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main"]
