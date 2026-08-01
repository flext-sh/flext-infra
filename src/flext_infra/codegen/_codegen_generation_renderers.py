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


# NOTE (multi-agent, mro-p68a.46.9 / agent: codex): generation renders and
# validates Python structure in-process. Generic formatting and analysis belong
# exclusively to the canonical fmt/fix/check verbs.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render codegen models through the canonical CLI template facade."""

    @staticmethod
    def _render_model(
        template_name: str, context: p.Model, *, target_filename: str
    ) -> str:
        """Render one deterministic typed Python artifact and validate syntax."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        rendered = u.Cli.template_render(
            template_root / template_name, context
        ).unwrap()
        rendered_output = rendered.rstrip() + "\n"
        compile(rendered_output, target_filename, "exec")
        return rendered_output


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
