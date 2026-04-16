"""Generate and validate base.mk files from templates."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraBaseMkTemplateEngine,
    FlextInfraConstantsBase,
    FlextInfraModelsBasemk,
    FlextInfraProtocolsBase,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


class FlextInfraBaseMkGenerator(s[str]):
    """Generate base.mk content and write to file or stream."""

    project_name: Annotated[
        str | None, m.Field(description="Optional project name override")
    ] = None
    output: Annotated[
        Path | None, m.Field(description="Optional file path for generated content")
    ] = None

    template_engine: Annotated[
        FlextInfraProtocolsBase.TemplateRenderer | None,
        m.Field(exclude=True, description="Template engine"),
    ] = None

    @property
    def _get_runner(self) -> p.Cli.CommandRunner:
        """Return the command runner."""
        return u.Cli()

    @override
    def execute(self) -> p.Result[str]:
        settings = (
            FlextInfraBaseMkTemplateEngine.default_config().model_copy(
                update={"project_name": self.project_name},
            )
            if self.project_name
            else None
        )
        result = self.generate_basemk(settings)
        if result.failure:
            return result
        write_result = self.write(
            result.value,
            output=self.output,
            stream=sys.stdout,
        )
        if write_result.failure:
            return r[str].fail(write_result.error or "write failed")
        return result

    def generate_basemk(
        self,
        settings: FlextInfraModelsBasemk.BaseMkConfig | t.ScalarMapping | None = None,
    ) -> p.Result[str]:
        """Generate base.mk content from configuration."""
        config_result = self._normalize_config(settings)
        if config_result.failure:
            return r[str].fail(config_result.error or "invalid base.mk configuration")
        config_value = config_result.value
        render_result = (
            self.template_engine or FlextInfraBaseMkTemplateEngine()
        ).render_all(config_value)
        if render_result.failure:
            return r[str].fail(render_result.error or "base.mk render failed")
        return self._validate_generated_output(render_result.value)

    def write(
        self,
        content: str,
        *,
        output: Path | None = None,
        stream: FlextInfraProtocolsBase.OutputStream | None = None,
    ) -> p.Result[bool]:
        """Write generated content to file or stream."""
        if output is None:
            target_stream = stream
            if target_stream is None:
                return r[bool].fail("stdout stream is required for console output")
            try:
                _ = target_stream.write(content)
                return r[bool].ok(True)
            except (OSError, ValueError) as exc:
                return r[bool].fail(f"base.mk stdout write failed: {exc}")
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            _ = output.write_text(
                content,
                encoding=FlextInfraConstantsBase.ENCODING_DEFAULT,
            )
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"base.mk write failed: {exc}")

    def _normalize_config(
        self,
        settings: FlextInfraModelsBasemk.BaseMkConfig | t.ScalarMapping | None,
    ) -> p.Result[FlextInfraModelsBasemk.BaseMkConfig]:
        if settings is None:
            return r[FlextInfraModelsBasemk.BaseMkConfig].ok(
                FlextInfraBaseMkTemplateEngine.default_config(),
            )
        if isinstance(settings, FlextInfraModelsBasemk.BaseMkConfig):
            return r[FlextInfraModelsBasemk.BaseMkConfig].ok(settings)
        try:
            normalized = FlextInfraModelsBasemk.BaseMkConfig.model_validate(
                dict(settings),
            )
            return r[FlextInfraModelsBasemk.BaseMkConfig].ok(normalized)
        except (TypeError, ValueError) as exc:
            return r[FlextInfraModelsBasemk.BaseMkConfig].fail(
                f"base.mk configuration validation failed: {exc}",
            )

    def _validate_generated_output(self, content: str) -> p.Result[str]:
        """Validate generated base.mk by running make --dry-run."""
        try:
            with tempfile.TemporaryDirectory(prefix="flext-basemk-") as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                base_mk_path = temp_dir / FlextInfraConstantsBase.BASE_MK
                makefile_path = temp_dir / FlextInfraConstantsBase.MAKEFILE_FILENAME
                _ = base_mk_path.write_text(
                    content,
                    encoding=FlextInfraConstantsBase.ENCODING_DEFAULT,
                )
                _ = makefile_path.write_text(
                    "include base.mk\n",
                    encoding=FlextInfraConstantsBase.ENCODING_DEFAULT,
                )
                process_result = self._get_runner.run([
                    FlextInfraConstantsBase.MAKE,
                    "-C",
                    str(temp_dir),
                    "--dry-run",
                    "help",
                ])
                if process_result.failure:
                    error_text = process_result.error or "make validation failed"
                    return r[str].fail(
                        f"generated base.mk validation failed: {error_text}",
                    )
        except OSError as exc:
            return r[str].fail(f"generated base.mk validation failed: {exc}")
        return r[str].ok(content)

    @staticmethod
    def render_bootstrap_include() -> p.Result[str]:
        """Render the Makefile bootstrap include block from template."""
        return FlextInfraBaseMkTemplateEngine().render_single(
            c.Infra.MAKEFILE_BOOTSTRAP_TEMPLATE,
            make=FlextInfraConstantsBase,
        )


__all__: list[str] = ["FlextInfraBaseMkGenerator"]
