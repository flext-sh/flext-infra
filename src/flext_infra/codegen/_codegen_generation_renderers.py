"""Template renderers for generated ``__init__`` files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from jinja2 import BaseLoader, TemplateNotFound
from jinja2.loaders import split_template_path

from flext_infra import FlextInfraConfig, u
from flext_infra.codegen import FlextInfraCodegenGenerationLazyEntriesMixin

if TYPE_CHECKING:
    from collections.abc import Callable

    from jinja2 import Environment

    from flext_infra import p


# Lazy generation delegates exact models to flext-cli. The composed producer
# prepares these bytes against the destination policy before publication.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin,
):
    """Render codegen models through the canonical CLI template facade."""

    class SourceLoader(BaseLoader):
        """Feed canonical Jinja exclusively from the shared original source owner."""

        def __init__(self, root: Path, project: p.Infra.RopeProject) -> None:
            self._root = root
            self._project = project

        @override
        def get_source(
            self,
            environment: Environment,
            template: str,
        ) -> tuple[str, str, Callable[[], bool] | None]:
            path = self._root.joinpath(*split_template_path(template))
            if not self._project.source_query(path, "isfile"):
                raise TemplateNotFound(template)
            return self._project.source_text(path), str(path), None

    @staticmethod
    def _template_path(template_name: str) -> Path:
        """Resolve one packaged lazy-init template source.

        Returns:
            The resulting ``Path``.

        Raises:
            ValueError: If lazy-init template escapes its source root.

        """
        template_root = (
            FlextInfraConfig.ssot_config_dir().parent / "templates"
        ).resolve()
        template_path = (template_root / template_name).resolve()
        if not template_path.is_relative_to(template_root):
            msg = f"lazy-init template escapes its source root: {template_name}"
            raise ValueError(msg)
        return template_path

    @staticmethod
    def _render_model(
        template_name: str,
        context: p.Model,
        *,
        target_filename: str,
        source_project: p.Infra.RopeProject | None = None,
    ) -> str:
        """Render one deterministic typed Python input for composed preparation.

        Returns:
            The resulting ``str``.

        """
        template_path = FlextInfraCodegenGenerationRenderersMixin._template_path(
            template_name,
        )
        rendered = (
            u.Cli.template_render(template_path, context).unwrap()
            if source_project is None
            else u.Cli
            .template_environment(template_path.parent)
            .overlay(
                loader=FlextInfraCodegenGenerationRenderersMixin.SourceLoader(
                    template_path.parent,
                    source_project,
                ),
            )
            .get_template(template_path.name)
            .render(context.model_dump(mode="json"))
        )
        compile(rendered, target_filename, "exec")
        return rendered.rstrip() + "\n"


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
