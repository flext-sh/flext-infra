"""Template renderers for generated ``__init__`` files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)

if TYPE_CHECKING:
    from flext_infra.protocols import p


# NOTE (multi-agent, mro-p4s3.2 / agent: uv_overlay_owner): lazy generation
# delegates its exact models to the sole flext-cli template engine.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin,
):
    """Render codegen models through the canonical CLI template facade."""

    @staticmethod
    def _render_model(template_name: str, context: p.Model) -> str:
        """Render a typed template context."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        return u.Cli.template_render(template_root / template_name, context).unwrap()


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
