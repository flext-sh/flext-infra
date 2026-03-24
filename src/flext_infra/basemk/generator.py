"""Generate and validate base.mk files from templates."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TextIO, override

from flext_infra import (
    FlextInfraBaseMkTemplateEngine,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)

_TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent / "templates"


class FlextInfraBaseMkGenerator(s[str]):
    """Generate base.mk content and write to file or stream."""

    def __init__(self, template_engine: p.Infra.TemplateRenderer | None = None) -> None:
        """Initialize the base.mk generator."""
        super().__init__(
            config_type=None,
            config_overrides=None,
            initial_context=None,
            subproject=None,
            services=None,
            factories=None,
            resources=None,
            container_overrides=None,
            wire_modules=None,
            wire_packages=None,
            wire_classes=None,
        )
        self._template_engine = template_engine or FlextInfraBaseMkTemplateEngine()

    @property
    def _get_runner(self) -> p.Infra.CommandRunner:
        """Return the command runner."""
        return u.Infra

    @override
    def execute(self) -> r[str]:
        return self.generate()

    @override
    def generate(
        self,
        config: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
    ) -> r[str]:
        """Generate base.mk content from configuration."""
        config_result = self._normalize_config(config)
        if config_result.is_failure:
            return r[str].fail(config_result.error or "invalid base.mk configuration")
        config_value = config_result.value
        render_result = self._template_engine.render_all(config_value)
        if render_result.is_failure:
            return r[str].fail(render_result.error or "base.mk render failed")
        return self._validate_generated_output(render_result.value)

    def write(
        self,
        content: str,
        *,
        output: Path | None = None,
        stream: TextIO | None = None,
    ) -> r[bool]:
        """Write generated content to file or stream."""
        if output is None:
            target_stream = stream
            if target_stream is None:
                return r[bool].fail("stdout stream is required for console output")
            try:
                _ = target_stream.write(content)
                return r[bool].ok(True)
            except OSError as exc:
                return r[bool].fail(f"base.mk stdout write failed: {exc}")
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            _ = output.write_text(content, encoding=c.Infra.Encoding.DEFAULT)
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"base.mk write failed: {exc}")

    def _normalize_config(
        self,
        config: m.Infra.BaseMkConfig | t.ScalarMapping | None,
    ) -> r[m.Infra.BaseMkConfig]:
        if config is None:
            return r[m.Infra.BaseMkConfig].ok(
                FlextInfraBaseMkTemplateEngine.default_config(),
            )
        if isinstance(config, m.Infra.BaseMkConfig):
            return r[m.Infra.BaseMkConfig].ok(config)
        try:
            normalized = m.Infra.BaseMkConfig.model_validate(
                dict(config.items()),
            )
            return r[m.Infra.BaseMkConfig].ok(normalized)
        except (TypeError, ValueError) as exc:
            return r[m.Infra.BaseMkConfig].fail(
                f"base.mk configuration validation failed: {exc}",
            )

    def _validate_generated_output(self, content: str) -> r[str]:
        """Validate generated base.mk by running make --dry-run."""
        try:
            with tempfile.TemporaryDirectory(prefix="flext-basemk-") as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                base_mk_path = temp_dir / c.Infra.Files.BASE_MK
                makefile_path = temp_dir / c.Infra.Files.MAKEFILE_FILENAME
                _ = base_mk_path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)
                _ = makefile_path.write_text(
                    "include base.mk\n",
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                process_result = self._get_runner.run([
                    c.Infra.Cli.MAKE,
                    "-C",
                    str(temp_dir),
                    "--dry-run",
                    "help",
                ])
                if process_result.is_failure:
                    error_text = process_result.error or "make validation failed"
                    return r[str].fail(
                        f"generated base.mk validation failed: {error_text}",
                    )
        except OSError as exc:
            return r[str].fail(f"generated base.mk validation failed: {exc}")
        return r[str].ok(content)

    @staticmethod
    def render_bootstrap_include() -> r[str]:
        """Render the Makefile bootstrap include block from template."""
        template_path = _TEMPLATES_DIR / c.Infra.MAKEFILE_BOOTSTRAP_TEMPLATE
        try:
            content = template_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            return r[str].ok(content.rstrip("\n"))
        except OSError as exc:
            return r[str].fail(f"bootstrap template read failed: {exc}")


__all__ = ["FlextInfraBaseMkGenerator"]
