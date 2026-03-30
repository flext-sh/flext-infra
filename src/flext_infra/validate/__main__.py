"""CLI entry point for validate."""

from __future__ import annotations

import sys

from flext_infra import t, u

# Backward-compat: tests import FlextInfraValidateCli from this module.
from flext_infra.validate.cli import FlextInfraCliValidate as FlextInfraValidateCli

_VALUE_FLAGS: frozenset[str] = frozenset({"--workspace"})


def _is_help_request(cli_args: list[str]) -> bool:
    """Return True if the args contain a help flag."""
    return any(arg in {"--help", "-h"} for arg in cli_args)


def main(argv: t.StrSequence | None = None) -> int:
    """Run validate CLI through direct Typer invocation."""
    from flext_cli import cli
    from flext_core import FlextRuntime

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="validate",
        help_text="Core infrastructure services",
    )
    mixin = FlextInfraValidateCli()
    mixin.register_validate(app)
    cli_args = u.Infra.reorder_argv(
        list(argv) if argv is not None else sys.argv[1:],
        value_flags=_VALUE_FLAGS,
    )
    if not cli_args:
        app(["--help"], standalone_mode=False)
        return 1
    if _is_help_request(cli_args):
        app(cli_args, standalone_mode=True)
        return 0
    try:
        app(cli_args, standalone_mode=True)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
