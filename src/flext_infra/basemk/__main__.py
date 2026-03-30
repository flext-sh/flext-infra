"""CLI entry point for base.mk generation utilities."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_cli import cli
from flext_core import FlextRuntime, r

from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkTemplateEngine,
    m,
    t,
)

# ── Helpers ──────────────────────────────────────────────────


def _build_config(project_name: str | None) -> m.Infra.BaseMkConfig | None:
    if project_name is None:
        return None
    return FlextInfraBaseMkTemplateEngine.default_config().model_copy(
        update={"project_name": project_name},
    )


# ── Router ───────────────────────────────────────────────────


class FlextInfraBaseMkCli:
    """Declarative CLI router for base.mk generation."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="basemk",
            help_text="base.mk generation utilities",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="basemk", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="generate",
                help_text="Generate base.mk content from templates",
                model_cls=m.Infra.BaseMkGenerateInput,
                handler=self._handle_generate,
                success_message="base.mk generation complete",
                failure_message="base.mk generation failed",
            ),
        )

    @staticmethod
    def _handle_generate(params: m.Infra.BaseMkGenerateInput) -> r[str]:
        """Generate base.mk content and optionally write to file."""
        generator = FlextInfraBaseMkGenerator()
        config = _build_config(params.project_name)
        generated_result = generator.generate_basemk(config)
        if generated_result.is_failure:
            return r[str].fail(
                generated_result.error or "base.mk generation failed",
            )
        output = Path(params.output) if params.output else None
        write_result = generator.write(
            generated_result.value,
            output=output,
            stream=sys.stdout,
        )
        if write_result.is_failure:
            return r[str].fail(write_result.error or "base.mk write failed")
        return r[str].ok(generated_result.value)


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Run the base.mk CLI entrypoint."""
    FlextRuntime.ensure_structlog_configured()
    result = FlextInfraBaseMkCli().run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
