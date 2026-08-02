"""Gitignore ownership for the layout engine apply path (mro-0wuz).

Every governed project converges through the canonical conform render (one
owner, one template). Invalid or external targets fail closed.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector


class FlextInfraCodegenLayoutGitignoreMixin:
    """Ensure the layout gitignore patterns for one project directory."""

    def _apply_gitignore(
        self, project_dir: Path
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Ensure gitignore patterns through the governed canonical render."""
        context = self._managed_context(project_dir)
        if context.failure:
            return r[t.Infra.LayoutStatus].fail(
                context.error or f"unable to resolve conform context: {project_dir}"
            )
        workspace, target = context.value
        return self._apply_gitignore_managed(project_dir, workspace, target)

    def _apply_gitignore_managed(
        self,
        project_dir: Path,
        workspace: m.Infra.WorkspaceSpec,
        target: m.Infra.RepositoryConformTarget,
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Write the canonical rendered gitignore for a governed project."""
        rendered = FlextInfraCodegenConform.render_project_gitignore(
            config.Infra.codegen,
            profile=target.make_profile,
            project_name=target.canonical_project_name,
            workspace=workspace,
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

    @staticmethod
    def _managed_context(
        project_dir: Path,
    ) -> p.Result[tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]]:
        """Resolve the typed workspace and repository conformance context."""
        workspace_root = FlextInfraWorkspaceDetector.resolve_workspace_root(project_dir)
        if workspace_root.failure:
            return r[
                tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].fail(
                workspace_root.error or f"unable to resolve workspace: {project_dir}"
            )
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            workspace_root.value
        )
        if workspace.failure:
            return r[
                tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].fail(
                workspace.error or f"unable to load workspace: {workspace_root.value}"
            )
        target = FlextInfraWorkspaceDetector.conform_target(
            project_dir, workspace.value
        )
        if target.failure:
            return r[
                tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].fail(
                target.error or f"unable to resolve conform target: {project_dir}"
            )
        return r[
            tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
        ].ok((workspace.value, target.value))


__all__: list[str] = ["FlextInfraCodegenLayoutGitignoreMixin"]
