"""CLI entry point for basemk."""

from __future__ import annotations

import sys

from flext_infra import FlextInfraBaseMkTemplateEngine, m, t


def _build_config(project_name: str | None) -> m.Infra.BaseMkConfig | None:
    """Build a BaseMkConfig from an optional project name override."""
    if project_name is None:
        return None
    return FlextInfraBaseMkTemplateEngine.default_config().model_copy(
        update={"project_name": project_name},
    )


def main(argv: t.StrSequence | None = None) -> int:
    """Run basemk CLI through direct Typer invocation."""
    from flext_cli import cli
    from flext_core import FlextRuntime

    from flext_infra.basemk.cli import FlextInfraCliBasemk

    FlextRuntime.ensure_structlog_configured()
    app = cli.create_app_with_common_params(
        name="basemk",
        help_text="base.mk generation utilities",
    )
    mixin = FlextInfraCliBasemk()
    mixin.register_basemk(app)
    cli_args = list(argv) if argv is not None else sys.argv[1:]
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
