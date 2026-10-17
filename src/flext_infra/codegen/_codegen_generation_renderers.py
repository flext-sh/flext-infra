"""Template renderers for generated ``__init__`` files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraConfig, m, u
from flext_infra.codegen import FlextInfraCodegenGenerationLazyEntriesMixin

if TYPE_CHECKING:
    from flext_infra import p


# Lazy generation delegates exact models to flext-cli. The composed producer
# prepares these bytes against the destination policy before publication.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin,
):
    """Render codegen models through the canonical CLI template facade."""

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
            .template_render_authenticated(
                m.Cli.TemplateRenderRequest(template=template_path),
                context,
                source_states=(source_project.source_state(template_path),),
            )
            .unwrap()
            .rendered
        )
        compile(rendered, target_filename, "exec")
        return rendered.rstrip() + "\n"


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
