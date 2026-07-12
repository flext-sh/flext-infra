"""Workspace Makefile template rendering helpers."""

from __future__ import annotations

from pathlib import Path

from jinja2.environment import Environment
from jinja2.exceptions import TemplateError
from jinja2.loaders import FileSystemLoader
from jinja2.runtime import StrictUndefined
from jinja2.utils import select_autoescape

from flext_core import r
from flext_infra.constants import c
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraWorkspaceMakefileTemplateMixin:
    """Template bootstrap and render operations for workspace Makefiles."""

    @property
    def template_path(self) -> Path:
        """Path to the Makefile Jinja2 template used for workspace generation."""
        template_name: str = c.Infra.MAKEFILE_TEMPLATE_NAME
        return Path(__file__).parent.parent / "templates" / template_name

    @staticmethod
    def _build_template_lines(content: str) -> str:
        """Transform raw Makefile content into a Jinja2 template string."""
        lines = content.splitlines(keepends=True)
        output: t.MutableSequenceOf[str] = []
        header_done = False
        for line in lines:
            header_done = (
                FlextInfraWorkspaceMakefileTemplateMixin._append_template_line(
                    output,
                    line,
                    header_done=header_done,
                )
            )
        template_content = "".join(output)
        return FlextInfraWorkspaceMakefileTemplateMixin._ensure_custom_include(
            template_content,
            content,
        )

    @staticmethod
    def _append_template_line(
        output: t.MutableSequenceOf[str],
        line: str,
        *,
        header_done: bool,
    ) -> bool:
        """Append one bootstrapped template line and return header state."""
        if not header_done and line.startswith("#"):
            output.extend(FlextInfraWorkspaceMakefileTemplateMixin._template_header())
            return True
        if not header_done and not line.strip():
            return False
        if line.startswith("PR_BRANCH ?="):
            output.append("PR_BRANCH ?= {{ pr_branch }}\n")
        else:
            output.append(line)
        return header_done

    @staticmethod
    def _template_header() -> t.StrSequence:
        """Return the generated workspace Makefile header."""
        return (
            "# =============================================================================\n",
            "# FLEXT Workspace Makefile\n",
            "# =============================================================================\n",
            f"{c.Infra.MAKEFILE_GENERATED_MARKER}\n",
            "# Run 'make sync' from workspace root to regenerate this file.\n",
            "# DO NOT EDIT — put custom targets in workspace_custom.mk instead.\n",
            "# =============================================================================\n",
        )

    @staticmethod
    def _ensure_custom_include(template_content: str, source_content: str) -> str:
        """Ensure the generated template includes workspace custom targets."""
        if c.Infra.MAKEFILE_CUSTOM_INCLUDE in source_content:
            return template_content
        content = (
            template_content
            if template_content.endswith("\n")
            else (template_content + "\n")
        )
        return (
            content
            + "\n"
            + "# Workspace-specific custom targets (optional, never overwritten by sync)\n"
            + f"{c.Infra.MAKEFILE_CUSTOM_INCLUDE}\n"
        )

    def _write_bootstrap_template(
        self,
        *,
        makefile: Path,
        pr_branch: str,
        template_content: str,
    ) -> p.Result[bool]:
        """Persist the generated template and rendered workspace Makefile."""
        _ = u.Cli.ensure_dir(Path(__file__).parent.parent / "templates")
        template_write = u.Cli.atomic_write_text_file(
            self.template_path,
            template_content,
        )
        if template_write.failure:
            return template_write
        render_result = self._render_template(
            pr_branch=pr_branch,
            template_text=template_content,
        )
        if render_result.failure:
            return r[bool].fail(render_result.error or "template render failed")
        return u.Cli.atomic_write_text_file(makefile, render_result.value)

    def _render_template(
        self,
        *,
        pr_branch: str,
        template_text: str | None = None,
    ) -> p.Result[str]:
        """Render the workspace Makefile template with canonical make metadata."""
        try:
            rendered = self._render_template_unchecked(
                pr_branch=pr_branch,
                template_text=template_text,
            )
        except (OSError, TemplateError, TypeError, ValueError) as exc:
            return r[str].fail_op("template render", exc)
        return r[str].ok(rendered)

    def _render_template_unchecked(
        self,
        *,
        pr_branch: str,
        template_text: str | None,
    ) -> str:
        """Render the workspace Makefile template without exception wrapping."""
        environment = Environment(
            loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates")),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True,
            undefined=StrictUndefined,
            autoescape=select_autoescape(),
        )
        template_obj: t.Infra.JinjaTemplate = (
            environment.get_template(c.Infra.MAKEFILE_TEMPLATE_NAME)
            if template_text is None
            else environment.from_string(template_text)
        )
        return self._render_template_content(template_obj, pr_branch=pr_branch)

    @staticmethod
    def _render_template_content(
        template: p.Infra.RenderableTemplate,
        *,
        pr_branch: str,
    ) -> str:
        """Render a validated template object into the final Makefile text."""
        rendered: str = template.render(
            pr_branch=pr_branch,
            make=c.Infra,
        )
        return rendered


__all__: list[str] = ["FlextInfraWorkspaceMakefileTemplateMixin"]
