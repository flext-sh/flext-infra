"""Generate and validate base.mk files from templates."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, p, r, s, t, u
from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine


class FlextInfraBaseMkGenerator(s[str]):
    """Generate base.mk content and write to file or stream."""

    project_name: Annotated[
        str | None, m.Field(description="Optional project name override")
    ] = None
    output: Annotated[
        Path | None, m.Field(description="Optional file path for generated content")
    ] = None

    template_engine: Annotated[
        p.Infra.TemplateRenderer | None,
        m.Field(exclude=True, description="Template engine"),
    ] = None

    @property
    def _get_runner(self) -> p.Cli.CommandRunner:
        """Return the command runner."""
        return u.Cli()

    @override
    def execute(self) -> p.Result[str]:
        """Execute."""
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
        settings: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
    ) -> p.Result[str]:
        """Generate base.mk content from configuration."""
        config_result = FlextInfraBaseMkTemplateEngine.normalize_config(settings)
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
        stream: p.Infra.OutputStream | None = None,
    ) -> p.Result[bool]:
        """Write generated content to file or stream."""
        if output is None:
            target_stream = stream
            if target_stream is None:
                return r[bool].fail("stdout stream is required for console output")
            try:
                _ = target_stream.write(content)
                return r[bool].ok(True)
            except c.EXC_OS_VALUE as exc:
                return r[bool].fail_op("base.mk stdout write", exc)
        return u.Cli.atomic_write_text_file(output, content)

    def _validate_generated_output(self, content: str) -> p.Result[str]:
        """Validate generated base.mk by running make --dry-run."""
        try:
            with tempfile.TemporaryDirectory(prefix="flext-basemk-") as temp_dir_name:
                validation = self._validate_generated_output_in_dir(
                    content,
                    Path(temp_dir_name),
                )
                if validation.failure:
                    return validation
        except OSError as exc:
            return r[str].fail_op("generated base.mk validation", exc)
        return r[str].ok(content)

    def _validate_generated_output_in_dir(
        self,
        content: str,
        temp_dir: Path,
    ) -> p.Result[str]:
        """Validate generated content inside an already-created temp directory."""
        write_result = self._write_validation_makefiles(content, temp_dir)
        if write_result.failure:
            return r[str].fail(write_result.error or "temp Makefile write failed")
        process_result = self._get_runner.run([
            c.Infra.MAKE,
            "-C",
            str(temp_dir),
            "--dry-run",
            "help",
        ])
        if process_result.failure:
            error_text = process_result.error or "make validation failed"
            return r[str].fail_op("generated base.mk validation", error_text)
        return r[str].ok(content)

    @staticmethod
    def _write_validation_makefiles(content: str, temp_dir: Path) -> p.Result[bool]:
        """Write temporary Makefile pair used by base.mk validation."""
        base_write = u.Cli.atomic_write_text_file(
            temp_dir / c.Infra.BASE_MK,
            content,
        )
        if base_write.failure:
            return r[bool].fail(base_write.error or "temp base.mk write failed")
        makefile_write = u.Cli.atomic_write_text_file(
            temp_dir / c.Infra.MAKEFILE_FILENAME,
            "include base.mk\n",
        )
        if makefile_write.failure:
            return r[bool].fail(makefile_write.error or "temp Makefile write failed")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraBaseMkGenerator"]
