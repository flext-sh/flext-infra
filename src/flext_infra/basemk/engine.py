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

from flext_infra import (
    FlextInfraConstantsBase,
    FlextInfraConstantsBasemk,
    FlextInfraModelsBasemk,
    FlextInfraProtocolsBase,
    FlextInfraTypesBase,
    p,
    r,
    s,
)


class FlextInfraBaseMkTemplateEngine(s[str]):
    """Render base.mk templates with configuration context."""

    _environment: FlextInfraTypesBase.JinjaEnvironment = PrivateAttr(
        default_factory=lambda: FlextInfraBaseMkTemplateEngine._build_environment(),
    )

    @staticmethod
    def _templates_dir() -> Path:
        """Resolve templates directory relative to this package."""
        return Path(__file__).resolve().parent.parent / "templates"

    @staticmethod
    def _build_environment() -> FlextInfraTypesBase.JinjaEnvironment:
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
    def default_config() -> FlextInfraModelsBasemk.BaseMkConfig:
        """Return default base.mk generation configuration."""
        return FlextInfraModelsBasemk.BaseMkConfig(
            project_name=FlextInfraConstantsBase.DEFAULT_UNNAMED,
            python_version="3.13",
            core_stack=FlextInfraConstantsBase.PYTHON,
            package_manager=FlextInfraConstantsBase.POETRY,
            source_dir=FlextInfraConstantsBase.DEFAULT_SRC_DIR,
            tests_dir=FlextInfraConstantsBase.DIR_TESTS,
            lint_gates=[
                FlextInfraConstantsBase.LINT,
                FlextInfraConstantsBase.FORMAT,
                FlextInfraConstantsBase.PYREFLY,
                FlextInfraConstantsBase.MYPY,
                FlextInfraConstantsBase.PYRIGHT,
            ],
            test_command=FlextInfraConstantsBase.PYTEST,
        )

    @override
    def execute(self) -> p.Result[str]:
        return self.render_all()

    @staticmethod
    def _render_template(
        template: FlextInfraProtocolsBase.RenderableTemplate,
        **kwargs: FlextInfraModelsBasemk.BaseMkConfig
        | FlextInfraTypesBase.InfraValue
        | type,
    ) -> str:
        return template.render(**kwargs)

    def render_all(
        self,
        settings: FlextInfraModelsBasemk.BaseMkConfig | None = None,
    ) -> p.Result[str]:
        """Render all base.mk templates into a single output string."""
        active_config = settings or self.default_config()
        lint_gates_csv = ",".join(active_config.lint_gates)
        sections: MutableSequence[str] = []
        try:
            for template_name in FlextInfraConstantsBasemk.TEMPLATE_ORDER:
                template: FlextInfraProtocolsBase.RenderableTemplate = (
                    self._environment.get_template(
                        template_name,
                    )
                )
                rendered = self._render_template(
                    template,
                    settings=active_config,
                    lint_gates_csv=lint_gates_csv,
                    make=FlextInfraConstantsBase,
                )
                sections.append(rendered.rstrip("\n"))
            content = "\n\n".join(sections).rstrip("\n") + "\n"
            return r[str].ok(content)
        except (TemplateError, ValueError, TypeError) as exc:
            return r[str].fail(f"base.mk template render failed: {exc}")

    def render_single(
        self,
        template_name: str,
        **kwargs: FlextInfraModelsBasemk.BaseMkConfig
        | FlextInfraTypesBase.InfraValue
        | type,
    ) -> p.Result[str]:
        """Render a single named template with the given context."""
        try:
            template: FlextInfraProtocolsBase.RenderableTemplate = (
                self._environment.get_template(
                    template_name,
                )
            )
            content = self._render_template(template, **kwargs)
            return r[str].ok(content.rstrip("\n"))
        except (TemplateError, OSError, ValueError, TypeError) as exc:
            return r[str].fail(f"template render failed: {exc}")


__all__: list[str] = ["FlextInfraBaseMkTemplateEngine"]
