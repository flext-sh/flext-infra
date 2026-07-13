"""Template renderers for generated ``__init__`` files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, u
from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


# NOTE (multi-agent, mro-p4s3.2 / agent: uv_overlay_owner): lazy generation
# delegates its exact models to the sole flext-cli template engine.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render codegen models through the canonical CLI template facade."""

    @staticmethod
    def _render_model(template_name: str, context: p.Model) -> str:
        """Render and deterministically format a typed Python artifact."""
        template_root = u.Infra.resource_root("templates")
        rendered = u.Cli.template_render(
            template_root / template_name, context
        ).unwrap()
        # FLEXT: formatter owns layout; import order remains semantic, never isort-fixed.
        format_result = u.Cli.run_raw(
            [c.Infra.RUFF, c.Infra.FORMAT, "--stdin-filename", c.Infra.INIT_PY, "-"],
            cwd=template_root,
            input_data=rendered.encode(c.Cli.ENCODING_DEFAULT),
        )
        if format_result.failure:
            raise ValueError(format_result.error or "ruff format failed")
        output = format_result.unwrap()
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            msg = f"ruff format failed ({output.exit_code}): {detail}"
            raise ValueError(msg)
        return output.stdout.rstrip() + "\n"


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
