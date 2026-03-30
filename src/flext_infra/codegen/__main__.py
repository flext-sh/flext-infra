"""CLI entry point for codegen."""

from __future__ import annotations

import sys

from flext_infra import t

# Backward-compat re-exports used by tests
from flext_infra.codegen.cli import (
    FlextInfraCliCodegen as FlextInfraCodegenCli,
)
from flext_infra.codegen.lazy_init import (
    FlextInfraCodegenLazyInit,
)

_VALUE_FLAGS: frozenset[str] = frozenset({"--workspace"})


def _reorder_argv(cli_args: list[str]) -> list[str]:
    """Move flags from before the subcommand to after it.

    Allows ``main(["--check", "lazy-init", ...])`` to work the same as
    ``main(["lazy-init", "--check", ...])``.
    """
    subcmd_idx = -1
    i = 0
    while i < len(cli_args):
        arg = cli_args[i]
        if not arg.startswith("-"):
            subcmd_idx = i
            break
        if arg in _VALUE_FLAGS and i + 1 < len(cli_args):
            i += 2
            continue
        i += 1
    if subcmd_idx <= 0:
        return cli_args
    return [cli_args[subcmd_idx], *cli_args[:subcmd_idx], *cli_args[subcmd_idx + 1 :]]


def main(argv: t.StrSequence | None = None) -> int:
    """Run codegen CLI.

    Invokes the Typer app in standalone mode so that usage errors
    (e.g. unknown flags) propagate as ``SystemExit(2)`` to the caller.
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    from flext_infra.codegen.cli import FlextInfraCliCodegen

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="codegen",
        help_text="Code generation tools for workspace standardization",
    )
    mixin = FlextInfraCliCodegen()
    mixin.register_codegen(app)
    cli_args = _reorder_argv(list(argv) if argv is not None else sys.argv[1:])
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


__all__ = ["FlextInfraCodegenCli", "FlextInfraCodegenLazyInit", "main"]
