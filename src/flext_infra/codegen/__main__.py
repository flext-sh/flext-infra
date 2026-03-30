"""CLI entry point for codegen."""

from __future__ import annotations

import sys

from flext_infra import t, u

# Backward-compat re-exports used by tests
from flext_infra.codegen.cli import (
    FlextInfraCliCodegen,
    FlextInfraCliCodegen as FlextInfraCodegenCli,
)
from flext_infra.codegen.lazy_init import (
    FlextInfraCodegenLazyInit,
)

_VALUE_FLAGS: frozenset[str] = frozenset({"--workspace"})


def main(argv: t.StrSequence | None = None) -> int:
    """Run codegen CLI through direct Typer invocation."""
    from flext_cli import cli
    from flext_core import FlextRuntime

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="codegen",
        help_text="Code generation tools for workspace standardization",
    )
    mixin = FlextInfraCliCodegen()
    mixin.register_codegen(app)
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


__all__ = ["FlextInfraCodegenCli", "FlextInfraCodegenLazyInit", "main"]
