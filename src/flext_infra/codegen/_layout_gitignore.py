"""Gitignore ownership for the layout engine apply path (flext-0wuz).

Codegen-managed projects converge through the canonical conform render (one
owner, one template); unmanaged or external projects receive idempotent
appends of the missing patterns only.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, p, r, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform


class FlextInfraCodegenLayoutGitignoreMixin:
    """Ensure the layout gitignore patterns for one project directory."""

    def _apply_gitignore(
        self, project_dir: Path, patterns: t.StrSequence
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Ensure gitignore patterns via the canonical render or appending."""
        managed = u.Infra.tool_flext_declared(project_dir)
        if managed.failure:
            return r[t.Infra.LayoutStatus].fail(
                managed.error or "managed-project detection failed"
            )
        if managed.value:
            return self._apply_gitignore_managed(project_dir)
        return self._apply_gitignore_append(project_dir, patterns)

    def _apply_gitignore_managed(
        self, project_dir: Path
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Write the canonical rendered gitignore for a governed project."""
        rendered = FlextInfraCodegenConform.render_project_gitignore(
            config.Infra.codegen, project_name=project_dir.name
        )
        if rendered.failure:
            return r[t.Infra.LayoutStatus].fail(
                rendered.error or "gitignore render failed"
            )
        gitignore_path = project_dir / c.Infra.GITIGNORE
        current = ""
        if gitignore_path.is_file():
            read = u.Cli.files_read_text(gitignore_path)
            if read.failure:
                return r[t.Infra.LayoutStatus].fail(
                    read.error or "gitignore read failed"
                )
            current = read.value
        if rendered.value == current:
            return r[t.Infra.LayoutStatus].ok("noop")
        written = u.Cli.atomic_write_text_file(gitignore_path, rendered.value)
        if written.failure:
            return r[t.Infra.LayoutStatus].fail(
                written.error or "gitignore write failed"
            )
        return r[t.Infra.LayoutStatus].ok("applied")

    def _apply_gitignore_append(
        self, project_dir: Path, patterns: t.StrSequence
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Append missing patterns for an unmanaged or external project."""
        gitignore_path = project_dir / c.Infra.GITIGNORE
        current = ""
        if gitignore_path.is_file():
            read = u.Cli.files_read_text(gitignore_path)
            if read.failure:
                return r[t.Infra.LayoutStatus].fail(
                    read.error or "gitignore read failed"
                )
            current = read.value
        covered = {line.strip() for line in current.splitlines()}
        missing = tuple(
            pattern
            for pattern in patterns
            if pattern not in covered and pattern.rstrip("/") not in covered
        )
        if not missing:
            return r[t.Infra.LayoutStatus].ok("noop")
        text = current
        if text and not text.endswith("\n"):
            text += "\n"
        if text:
            text += "\n"
        text += f"# {c.Infra.GITIGNORE_LAYOUT_SECTION_NAME}\n"
        text += "\n".join(missing) + "\n"
        written = u.Cli.atomic_write_text_file(gitignore_path, text)
        if written.failure:
            return r[t.Infra.LayoutStatus].fail(
                written.error or "gitignore write failed"
            )
        return r[t.Infra.LayoutStatus].ok("applied")


__all__: list[str] = ["FlextInfraCodegenLayoutGitignoreMixin"]
