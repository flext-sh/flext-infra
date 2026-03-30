"""CLI entry point for documentation services.

Usage:
    python -m flext_infra.docs audit --workspace flext-core
    python -m flext_infra.docs fix --workspace flext-core --apply
    python -m flext_infra.docs build --workspace flext-core
    python -m flext_infra.docs generate --workspace flext-core --apply
    python -m flext_infra.docs validate --workspace flext-core

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys

from flext_infra import t, u
from flext_infra.docs.cli import FlextInfraCliDocs, FlextInfraDocsCli

__all__ = ["FlextInfraDocsCli", "main"]

_VALUE_FLAGS: frozenset[str] = frozenset({
    "--workspace",
    "--project",
    "--projects",
    "--output-dir",
})


def main(argv: t.StrSequence | None = None) -> int:
    """Run docs CLI through direct Typer invocation."""
    from flext_cli import cli
    from flext_core import FlextRuntime

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="docs",
        help_text="Documentation management services",
    )
    mixin = FlextInfraCliDocs()
    mixin.register_docs(app)
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
