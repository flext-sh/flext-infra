"""Workspace root Makefile generator.

Manages the root ``Makefile`` in a FLEXT workspace.  The file is
100% generated from a Jinja2 template stored inside ``flext_infra``.
Custom workspace targets go in ``workspace_custom.mk`` (auto-included).

Bootstrap flow (first run, no template yet):
  - Reads the current ``Makefile`` and registers it as the canonical template.
  - Adds ``@generated`` header and ``-include workspace_custom.mk``.
  - Parameterises ``PR_BRANCH`` from the current git branch.

Subsequent runs:
  - Reads the stored template, renders ``{{ pr_branch }}``.
  - SHA-256 idempotency skips writes when content is unchanged.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from pathlib import Path

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)

from flext_infra import c, p, r, t, u


class FlextInfraWorkspaceMakefileGenerator:
    """Generate and keep the workspace root Makefile in sync with flext_infra.

    The canonical source of truth is
    ``flext_infra/templates/workspace_makefile.mk.j2``.  Edit that file
    to change workspace-level verbs; then run ``make sync`` to propagate.
    """

    @property
    def template_path(self) -> Path:
        """Path to the Makefile Jinja2 template used for workspace generation."""
        return (
            Path(__file__).parent.parent / "templates" / c.Infra.MAKEFILE_TEMPLATE_NAME
        )

    def generate(self, workspace_root: Path) -> p.Result[bool]:
        """Regenerate the workspace root Makefile from the stored template.

        Args:
            workspace_root: Path to the workspace root (contains Makefile).

        Returns:
            r with True if Makefile was written, False if unchanged,
            failure on I/O error.

        """
        makefile = workspace_root / c.Infra.MAKEFILE_FILENAME

        if not self.template_path.exists():
            return self._bootstrap_template(makefile)

        pr_branch = self._current_branch(workspace_root)
        render_result = self._render_template(pr_branch=pr_branch)
        if render_result.failure:
            return r[bool].fail(render_result.error or "template render failed")
        content = render_result.value

        if makefile.exists():
            try:
                existing = makefile.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            except OSError as exc:
                return r[bool].fail(f"Makefile read failed: {exc}")
            if u.Cli.sha256_content(existing) == u.Cli.sha256_content(content):
                return r[bool].ok(False)

        return u.Cli.atomic_write_text_file(makefile, content)

    @staticmethod
    def _build_template_lines(content: str) -> str:
        """Transform raw Makefile content into a Jinja2 template string."""
        lines = content.splitlines(keepends=True)
        out: MutableSequence[str] = []
        header_done = False
        for line in lines:
            if not header_done and line.startswith("#"):
                out.extend((
                    "# =============================================================================\n",
                    "# FLEXT Workspace Makefile\n",
                    "# =============================================================================\n",
                    f"{c.Infra.MAKEFILE_GENERATED_MARKER}\n",
                    "# Run 'make sync' from workspace root to regenerate this file.\n",
                    "# DO NOT EDIT — put custom targets in workspace_custom.mk instead.\n",
                    "# =============================================================================\n",
                ))
                header_done = True
                continue
            if not header_done and not line.strip():
                continue
            if line.startswith("PR_BRANCH ?="):
                out.append("PR_BRANCH ?= {{ pr_branch }}\n")
                continue
            out.append(line)
        template_content = "".join(out)
        if c.Infra.MAKEFILE_CUSTOM_INCLUDE not in content:
            if not template_content.endswith("\n"):
                template_content += "\n"
            template_content += f"\n# Workspace-specific custom targets (optional, never overwritten by sync)\n{c.Infra.MAKEFILE_CUSTOM_INCLUDE}\n"
        return template_content

    def _bootstrap_template(self, makefile: Path) -> p.Result[bool]:
        """Create the template from the current Makefile (one-time bootstrap)."""
        if not makefile.exists():
            return r[bool].ok(False)
        try:
            content = makefile.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        except OSError as exc:
            return r[bool].fail(f"Makefile read failed: {exc}")
        if c.Infra.MAKEFILE_GENERATED_MARKER in content:
            return r[bool].ok(False)

        pr_branch = self._current_branch(makefile.parent)
        template_content = self._build_template_lines(content)

        try:
            _ = u.Cli.ensure_dir(Path(__file__).parent.parent / "templates")
            template_write = u.Cli.atomic_write_text_file(
                self.template_path, template_content
            )
            if template_write.failure:
                return template_write
        except OSError as exc:
            return r[bool].fail(f"template bootstrap failed: {exc}")

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
            environment = Environment(
                loader=FileSystemLoader(
                    str(Path(__file__).parent.parent / "templates")
                ),
                trim_blocks=False,
                lstrip_blocks=False,
                keep_trailing_newline=True,
                undefined=StrictUndefined,
                autoescape=select_autoescape(),
            )
            if template_text is None:
                template_obj: t.Infra.JinjaTemplate = environment.get_template(
                    c.Infra.MAKEFILE_TEMPLATE_NAME
                )
            else:
                template_obj = environment.from_string(template_text)
            rendered = self._render_template_content(
                template_obj,
                pr_branch=pr_branch,
            )
            return r[str].ok(rendered)
        except (OSError, TemplateError, TypeError, ValueError) as exc:
            return r[str].fail(f"template render failed: {exc}")

    @staticmethod
    def _render_template_content(
        template: p.Infra.RenderableTemplate,
        *,
        pr_branch: str,
    ) -> str:
        """Render a validated template object into the final Makefile text."""
        return template.render(
            pr_branch=pr_branch,
            make=c.Infra,
        )

    @staticmethod
    def _current_branch(workspace_root: Path) -> str:
        """Return current git branch or version from pyproject.toml."""
        capture_result = u.Cli.capture(
            ["git", "-C", str(workspace_root), "rev-parse", "--abbrev-ref", "HEAD"],
            timeout=5,
        )
        if capture_result.success:
            branch = capture_result.value
            if branch and branch != c.Infra.GIT_HEAD:
                return branch

        # Fallback: read version from pyproject.toml
        pyproject = workspace_root / c.Infra.PYPROJECT_FILENAME
        data_result = u.Cli.toml_read_json(pyproject)
        if data_result.success:
            data = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(data_result.value)
            project_raw = data.get("project")
            if isinstance(project_raw, dict):
                version_raw = project_raw.get("version", c.Infra.GIT_MAIN)
                if isinstance(version_raw, str):
                    return version_raw
        return c.Infra.GIT_MAIN


__all__: list[str] = ["FlextInfraWorkspaceMakefileGenerator"]
