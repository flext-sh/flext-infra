"""CLI entry point for github."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from flext_infra import t, u

# Backward-compat re-exports used by tests
from flext_infra.github.cli import (
    FlextInfraCliGithub as FlextInfraGithubCli,  # noqa: F401
)

_VALUE_FLAGS: frozenset[str] = frozenset({"--workspace"})


def run_pr(argv: Sequence[str]) -> int:
    """Run the pr subcommand (extracted for testability)."""
    from flext_cli import cli
    from flext_core import FlextRuntime

    from flext_infra.github.cli import FlextInfraCliGithub

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="github-pr",
        help_text="Manage pull requests for a single project",
    )
    mixin = FlextInfraCliGithub()
    mixin.register_github(app)
    try:
        app(list(argv), standalone_mode=True)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    return 0


def main(argv: t.StrSequence | None = None) -> int:
    """Run github CLI.

    Invokes the Typer app in standalone mode so that usage errors
    (e.g. unknown flags) propagate as ``SystemExit(2)`` to the caller.
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    from flext_infra.github.cli import FlextInfraCliGithub

    FlextRuntime.ensure_structlog_configured()
    cli_args = u.Infra.reorder_argv(
        list(argv) if argv is not None else sys.argv[1:],
        value_flags=_VALUE_FLAGS,
    )
    # Dispatch "pr" subcommand through run_pr for testability.
    main_mod = sys.modules[__name__]
    if cli_args and cli_args[0] == "pr":
        return getattr(main_mod, "run_pr")(cli_args[1:])
    app = cli.create_app_with_common_params(
        name="github",
        help_text="GitHub integration services",
    )
    app.info.context_settings = {"help_option_names": ["--help", "-h"]}
    mixin = FlextInfraCliGithub()
    mixin.register_github(app)
    if not cli_args:
        app(["--help"], standalone_mode=False)
        return 1
    try:
        app(cli_args, standalone_mode=True)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
