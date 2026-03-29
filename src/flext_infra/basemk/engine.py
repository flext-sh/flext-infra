"""Jinja2-based template engine for rendering base.mk configuration."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import Protocol, override

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)

from flext_infra import c, m, r, s, t


class _Renderable(Protocol):
    def render(
        self,
        **kwargs: m.Infra.BaseMkConfig | t.Infra.InfraValue,
    ) -> str: ...


def _render(
    template: _Renderable,
    **kwargs: m.Infra.BaseMkConfig | t.Infra.InfraValue,
) -> str:
    """Render a jinja2 template with explicit str return type."""
    return template.render(**kwargs)


class FlextInfraBaseMkTemplateEngine(s[str]):
    """Render base.mk templates with configuration context."""

    def __init__(self) -> None:
        """Initialize template environment for base.mk rendering."""
        super().__init__()
        template_root = Path(__file__).resolve().parent.parent / "templates"
        self._environment = Environment(
            loader=FileSystemLoader(str(template_root)),
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

    def render_all(self, config: m.Infra.BaseMkConfig | None = None) -> r[str]:
        """Render all base.mk templates into a single output string."""
        active_config = config or self.default_config()
        lint_gates_csv = ",".join(active_config.lint_gates)
        sections: MutableSequence[str] = []
        try:
            for template_name in c.Infra.TEMPLATE_ORDER:
                template = self._environment.get_template(template_name)
                rendered = _render(
                    template,
                    config=active_config,
                    lint_gates_csv=lint_gates_csv,
                )
                sections.append(rendered.rstrip("\n"))
            content = "\n\n".join(sections).rstrip("\n") + "\n"
            return r[str].ok(content)
        except (TemplateError, ValueError, TypeError) as exc:
            return r[str].fail(f"base.mk template render failed: {exc}")


__all__ = ["FlextInfraBaseMkTemplateEngine"]
