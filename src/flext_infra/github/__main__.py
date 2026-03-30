"""CLI entry point for github."""

from __future__ import annotations

import sys

from flext_infra import t

# Backward-compat re-exports used by tests
from flext_infra.github.cli import (
    FlextInfraCliGithub as FlextInfraGithubCli,  # noqa: F401
)


def main(argv: t.StrSequence | None = None) -> int:
    """Run github CLI.

    Uses ``cli.execute_app`` to normalize Typer exit behavior into ``r[bool]``
    so callers get an integer exit code (0 = success, 1 = failure, 2 = usage).
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    from flext_infra.github.cli import FlextInfraCliGithub

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="github",
        help_text="GitHub integration services",
    )
    mixin = FlextInfraCliGithub()
    mixin.register_github(app)
    result = cli.execute_app(app, prog_name="github", args=argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
