"""Jinja2-based template engine for rendering base.mk configuration."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import override

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)
from pydantic import PrivateAttr

from flext_infra import c, m, p, r, s, t


class FlextInfraBaseMkTemplateEngine(s[str]):
    """Render base.mk templates with configuration context."""

    _environment: t.Infra.JinjaEnvironment = PrivateAttr(
        default_factory=lambda: FlextInfraBaseMkTemplateEngine._build_environment(),
    )

    @staticmethod
    def _templates_dir() -> Path:
        """Resolve templates directory relative to this package."""
        return Path(__file__).resolve().parent.parent / "templates"

    @staticmethod
    def _build_environment() -> t.Infra.JinjaEnvironment:
        """Create the shared Jinja environment for base.mk rendering."""
        return Environment(
            loader=FileSystemLoader(
                str(FlextInfraBaseMkTemplateEngine._templates_dir()),
            ),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True,
            undefined=StrictUndefined,
            autoescape=select_autoescape(),
        )

    @staticmethod
    def default_config() -> m.Infra.BaseMkConfig:
        """Return default base.mk generation configuration."""
        return m.Infra.BaseMkConfig(
            project_name=c.Infra.Defaults.UNNAMED,
            python_version="3.13",
            core_stack=c.Infra.PYTHON,
            package_manager=c.Infra.POETRY,
            source_dir=c.Infra.Paths.DEFAULT_SRC_DIR,
            tests_dir=c.Infra.Directories.TESTS,
            lint_gates=[
                c.Infra.LINT,
                c.Infra.FORMAT,
                c.Infra.PYREFLY,
                c.Infra.MYPY,
                c.Infra.PYRIGHT,
            ],
            test_command=c.Infra.PYTEST,
        )

    @override
    def execute(self) -> r[str]:
        return self.render_all()

    @staticmethod
    def _render_template(
        template: p.Infra.RenderableTemplate,
        **kwargs: m.Infra.BaseMkConfig | t.Infra.InfraValue | type,
    ) -> str:
        return template.render(**kwargs)

    def render_all(self, config: m.Infra.BaseMkConfig | None = None) -> r[str]:
        """Render all base.mk templates into a single output string."""
        active_config = config or self.default_config()
        lint_gates_csv = ",".join(active_config.lint_gates)
        sections: MutableSequence[str] = []
        try:
            for template_name in c.Infra.TEMPLATE_ORDER:
                template: p.Infra.RenderableTemplate = self._environment.get_template(
                    template_name,
                )
                rendered = self._render_template(
                    template,
                    config=active_config,
                    lint_gates_csv=lint_gates_csv,
                    make=c.Infra.Make,
                )
                sections.append(rendered.rstrip("\n"))
            content = "\n\n".join(sections).rstrip("\n") + "\n"
            return r[str].ok(content)
        except (TemplateError, ValueError, TypeError) as exc:
            return r[str].fail(f"base.mk template render failed: {exc}")

    def render_single(
        self,
        template_name: str,
        **kwargs: m.Infra.BaseMkConfig | t.Infra.InfraValue | type,
    ) -> r[str]:
        """Render a single named template with the given context."""
        try:
            template: p.Infra.RenderableTemplate = self._environment.get_template(
                template_name,
            )
            content = self._render_template(template, **kwargs)
            return r[str].ok(content.rstrip("\n"))
        except (TemplateError, OSError, ValueError, TypeError) as exc:
            return r[str].fail(f"template render failed: {exc}")


__all__ = ["FlextInfraBaseMkTemplateEngine"]
