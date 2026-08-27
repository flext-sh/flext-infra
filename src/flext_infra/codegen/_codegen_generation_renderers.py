"""Template renderers for generated ``__init__`` files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, t, u
from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


# NOTE (multi-agent, flext-wkii.17.26 / agent: codex): lazy generation delegates
# exact models to flext-cli and proves every rendered initializer is Ruff-clean.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render codegen models through the canonical CLI template facade."""

    @staticmethod
    def _render_model(
        template_name: str, context: p.Model, *, target_filename: str
    ) -> str:
        """Render and deterministically format a typed Python artifact."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        rendered = u.Cli.template_render(
            template_root / template_name, context
        ).unwrap()
        compile(rendered, target_filename, "exec")
        organize_result = u.Cli.run_raw(
            [
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--fix-only",
                "--stdin-filename",
                target_filename,
                "-",
            ],
            cwd=template_root,
            input_data=rendered.encode(c.Cli.ENCODING_DEFAULT),
        )
        if organize_result.failure:
            raise ValueError(organize_result.error or "ruff import organization failed")
        organized = organize_result.unwrap()
        if organized.exit_code != 0:
            detail = (organized.stderr or organized.stdout).strip()
            msg = f"ruff import organization failed ({organized.exit_code}): {detail}"
            raise ValueError(msg)
        format_result = u.Cli.run_raw(
            [c.Infra.RUFF, c.Infra.FORMAT, "--stdin-filename", target_filename, "-"],
            cwd=template_root,
            input_data=organized.stdout.encode(c.Cli.ENCODING_DEFAULT),
        )
        if format_result.failure:
            raise ValueError(format_result.error or "ruff format failed")
        output = format_result.unwrap()
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            msg = f"ruff format failed ({output.exit_code}): {detail}"
            raise ValueError(msg)
        rendered_output: str = (
            t.Infra.STR_ADAPTER.validate_python(output.stdout).rstrip() + "\n"
        )
        return rendered_output


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
