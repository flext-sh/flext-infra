"""Jinja2-based template engine for rendering base.mk configuration."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from pathlib import Path
from typing import override

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)

from flext_infra import (
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)


class FlextInfraBaseMkTemplateEngine(s[str]):
    """Render base.mk templates with configuration context."""

    _environment: t.Infra.JinjaEnvironment = u.PrivateAttr(
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
            project_name=c.Infra.DEFAULT_UNNAMED,
            python_version="3.13",
            core_stack=c.Infra.PYTHON,
            package_manager=c.Infra.POETRY,
            source_dir=c.Infra.DEFAULT_SRC_DIR,
            tests_dir=c.Infra.DIR_TESTS,
            lint_gates=[
                c.Infra.LINT,
                c.Infra.FORMAT,
                c.Infra.PYREFLY,
                c.Infra.MYPY,
                c.Infra.PYRIGHT,
            ],
            test_command=c.Infra.PYTEST,
        )

    @staticmethod
    def normalize_config(
        settings: m.Infra.BaseMkConfig | t.ScalarMapping | None,
    ) -> p.Result[m.Infra.BaseMkConfig]:
        """Normalize user-provided config to the canonical BaseMk model."""
        if settings is None:
            return r[m.Infra.BaseMkConfig].ok(
                FlextInfraBaseMkTemplateEngine.default_config(),
            )
        if isinstance(settings, m.Infra.BaseMkConfig):
            return r[m.Infra.BaseMkConfig].ok(settings)
        try:
            normalized = m.Infra.BaseMkConfig.model_validate(
                dict(settings),
            )
            return r[m.Infra.BaseMkConfig].ok(normalized)
        except (TypeError, ValueError) as exc:
            return r[m.Infra.BaseMkConfig].fail(
                f"base.mk configuration validation failed: {exc}",
            )

    @staticmethod
    def render_bootstrap_include() -> p.Result[str]:
        """Render the canonical Makefile bootstrap include block."""
        return FlextInfraBaseMkTemplateEngine().render_single(
            c.Infra.MAKEFILE_BOOTSTRAP_TEMPLATE,
            make=c.Infra,
        )

    @override
    def execute(self) -> p.Result[str]:
        return self.render_all()

    @staticmethod
    def _render_template(
        template: p.Infra.RenderableTemplate,
        **kwargs: m.Infra.BaseMkConfig | t.Infra.InfraValue | type,
    ) -> str:
        rendered: str = template.render(**kwargs)
        return rendered

    def render_all(
        self,
        settings: m.Infra.BaseMkConfig | None = None,
    ) -> p.Result[str]:
        """Render all base.mk templates into a single output string."""
        active_config = settings or self.default_config()
        lint_gates_csv = ",".join(active_config.lint_gates)
        sections: MutableSequence[str] = []
        try:
            for template_name in c.Infra.TEMPLATE_ORDER:
                template: p.Infra.RenderableTemplate = self._environment.get_template(
                    template_name,
                )
                rendered = self._render_template(
                    template,
                    settings=active_config,
                    lint_gates_csv=lint_gates_csv,
                    make=c.Infra,
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
    ) -> p.Result[str]:
        """Render a single named template with the given context."""
        try:
            template: p.Infra.RenderableTemplate = self._environment.get_template(
                template_name,
            )
            content = self._render_template(template, **kwargs)
            return r[str].ok(content.rstrip("\n"))
        except (TemplateError, OSError, ValueError, TypeError) as exc:
            return r[str].fail(f"template render failed: {exc}")


__all__: list[str] = ["FlextInfraBaseMkTemplateEngine"]
