"""Template renderers for generated ``__init__`` files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja2.runtime import StrictUndefined
from jinja2.utils import select_autoescape

from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.protocols import p
    from flext_infra.typings import t


# mro-i6nq.10: Renderers consume only the canonical manifest/thin/eager models.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin,
):
    """Jinja-backed renderer helper methods."""

    @classmethod
    @override
    def _render_model(cls, template_name: str, context: m.ArbitraryTypesModel) -> str:
        """Render a typed template context with normalized trailing newline."""
        template = cls.get_template(template_name)
        rendered: str = template.render(**context.model_dump(mode="python"))
        return rendered.rstrip() + "\n"

    @staticmethod
    def _build_env() -> t.Infra.JinjaEnvironment:
        """Create a Jinja2 environment for codegen templates."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        return Environment(
            loader=FileSystemLoader(str(template_root)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
            undefined=StrictUndefined,
            autoescape=select_autoescape(),
        )

    _env: t.Infra.JinjaEnvironment | None = None

    @classmethod
    def get_template(cls, name: str) -> p.Infra.RenderableTemplate:
        """Return a template narrowed to the local render protocol."""
        env = cls._env
        if env is None:
            env = cls._build_env()
            cls._env = env
        return env.get_template(name)


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
