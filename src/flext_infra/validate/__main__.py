"""CLI entry point for validate."""

from __future__ import annotations

import sys

from flext_infra import t

# Backward-compat: tests import FlextInfraValidateCli from this module.
from flext_infra.validate.cli import FlextInfraCliValidate as FlextInfraValidateCli


def main(argv: t.StrSequence | None = None) -> int:
    """Run validate CLI.

    Invokes the Typer app via execute_app so that usage errors
    are normalized into ``r[bool]`` results.
    """
    from flext_cli import cli
    from flext_core import FlextRuntime

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="validate",
        help_text="Core infrastructure services",
    )
    mixin = FlextInfraValidateCli()
    mixin.register_validate(app)
    result = cli.execute_app(app, prog_name="validate", args=argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
