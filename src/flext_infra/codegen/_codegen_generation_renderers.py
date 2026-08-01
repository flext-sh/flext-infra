"""Template renderers for generated ``__init__`` files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import u
from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render codegen models through the canonical CLI template facade."""

    @staticmethod
    def _render_model(
        template_name: str, context: p.Model, *, target_filename: str
    ) -> str:
        """Render a deterministic typed Python artifact without running gates."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        rendered = u.Cli.template_render(
            template_root / template_name, context
        ).unwrap()
        compile(rendered, target_filename, "exec")
        return rendered.rstrip() + "\n"


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
