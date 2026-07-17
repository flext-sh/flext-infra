"""Template renderers for generated ``__init__`` files.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, p, u
from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)


# NOTE (multi-agent, mro-wkii.17.26 / agent: codex): lazy generation delegates
# exact models to flext-cli and proves every rendered initializer is Ruff-clean.
class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render codegen models through the canonical CLI template facade."""

    @staticmethod
    def _render_model(
        template_name: str, context: p.BaseModel, *, target_filename: str
    ) -> str:
        """Render and deterministically format a typed Python artifact."""
        template_root = u.Infra.resource_root("templates")
        rendered = u.Cli.template_render(
            template_root / template_name, context
        ).unwrap()
        # mro-wkii.17.27 (codex): formatting is explicit; lint never mutates output.
        compile(rendered, target_filename, "exec")
        format_result = u.Cli.run_raw(
            [c.Infra.RUFF, c.Infra.FORMAT, "--stdin-filename", target_filename, "-"],
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
        formatted = output.stdout.rstrip() + "\n"
        check_result = u.Cli.run_raw(
            [
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--no-fix",
                "--stdin-filename",
                target_filename,
                "-",
            ],
            cwd=template_root,
            input_data=formatted.encode(c.Cli.ENCODING_DEFAULT),
        )
        if check_result.failure:
            raise ValueError(check_result.error or "ruff check failed")
        checked = check_result.unwrap()
        if checked.exit_code != 0:
            detail = (checked.stderr or checked.stdout).strip()
            msg = f"generated initializer failed Ruff ({checked.exit_code}): {detail}"
            raise ValueError(msg)
        return formatted


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
