"""CLI entry point for refactor."""

from __future__ import annotations

import sys

from flext_infra import t, u

# Backward-compat re-exports used by tests
from flext_infra.refactor.cli import (
    FlextInfraCliRefactor as FlextInfraRefactorCli,
)

_VALUE_FLAGS: frozenset[str] = frozenset({"--workspace"})


def main(argv: t.StrSequence | None = None) -> int:
    """Run refactor CLI.

    Invokes the Typer app in standalone mode so that usage errors
    (e.g. unknown flags) propagate as ``SystemExit(2)`` to the caller.
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="refactor",
        help_text="Refactor and modernization tools for flext workspace",
    )
    mixin = FlextInfraRefactorCli()
    mixin.register_refactor(app)
    cli_args = u.Infra.reorder_argv(
        list(argv) if argv is not None else sys.argv[1:],
        value_flags=_VALUE_FLAGS,
    )
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


__all__ = ["FlextInfraRefactorCli", "main"]
