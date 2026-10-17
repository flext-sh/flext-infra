"""Gitignore ownership for the layout engine apply path.

Codegen-managed projects converge through the canonical conform render (one
owner, one template); unmanaged or external projects receive idempotent
appends of the missing patterns only.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLayoutPlanMixin,
    FlextInfraMiseArtifactsVerification,
    FlextInfraMisePublication,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenLayoutGitignoreMixin:
    """Ensure the layout gitignore patterns for one project directory."""

    def _apply_gitignore(
        self,
        project_dir: Path,
        patterns: t.StrSequence,
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Ensure gitignore patterns via the canonical render or appending.

        Derive content from the same captured state carried into publication.

        Returns:
            The resulting ``p.Result[t.Infra.LayoutStatus]``.

        """
        managed = self._managed_profile(project_dir)
        if managed.failure:
            return r[t.Infra.LayoutStatus].from_failure(managed)
        profile = managed.value
        gitignore_path = project_dir / c.Infra.GITIGNORE
        before = u.Cli.atomic_read_binary_file_state(gitignore_path, required=False)
        if before.failure:
            return r[t.Infra.LayoutStatus].from_failure(before)
        current = (
            ""
            if before.value.content is None
            else before.value.content.decode(c.DEFAULT_ENCODING)
        )
        if profile is None:
            desired = self._gitignore_append_content(current, patterns)
        else:
            rendered = u.Infra.render_project_gitignore(
                config.Infra.codegen,
                profile=profile,
                project_name=FlextInfraCodegenLayoutPlanMixin.layout_project_name(
                    project_dir,
                ),
                project_dir=project_dir,
            )
            if rendered.failure:
                return r[t.Infra.LayoutStatus].from_failure(rendered)
            desired = rendered.value
        if desired == current:
            noop_status: t.Infra.LayoutStatus = "noop"
            return FlextInfraMiseArtifactsVerification.states_current(
                (before.value,),
            ).map(lambda _: noop_status)
        planned = m.Infra.CodegenFilePlan(
            project=project_dir,
            path=gitignore_path,
            before=before.value,
            desired_content=desired.encode(c.DEFAULT_ENCODING),
            desired_mode=config.Infra.codegen.modes.file_default,
            owner="codegen",
            policy="full" if profile is not None else "merge",
        )
        written = FlextInfraMisePublication.publish_file_plan(
            planned,
            phase=c.Infra.CodegenStagedFilePhase.LAYOUT,
        )
        if written.failure:
            return r[t.Infra.LayoutStatus].from_failure(written)
        applied_status: t.Infra.LayoutStatus = "applied"
        return r[t.Infra.LayoutStatus].ok(applied_status)

    @staticmethod
    def _gitignore_append_content(
        current: str,
        patterns: t.StrSequence,
    ) -> str:
        """Derive missing layout patterns from the captured gitignore text.

        Returns:
            The original text or its extension with the missing patterns.

        """
        covered = {line.strip() for line in current.splitlines()}
        missing = tuple(
            pattern
            for pattern in patterns
            if pattern not in covered and pattern.rstrip("/") not in covered
        )
        if not missing:
            return current
        text = current
        if text and not text.endswith("\n"):
            text += "\n"
        if text:
            text += "\n"
        text += f"# {c.Infra.GITIGNORE_LAYOUT_SECTION_NAME}\n"
        text += "\n".join(missing) + "\n"
        return text

    @staticmethod
    def _managed_profile(project_dir: Path) -> p.Result[c.Infra.MakeProfile | None]:
        """Make profile when the project is governed by a workspace.

        Returns:
            The resulting ``p.Result[c.Infra.MakeProfile | None]``.

        """
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            u.Infra.resolve_repository_root_or_cwd(project_dir),
        )
        if workspace.failure:
            return r[c.Infra.MakeProfile | None].from_failure(workspace)
        target = FlextInfraWorkspaceDetector.conform_target(
            project_dir,
            workspace.value,
        )
        if target.failure:
            return r[c.Infra.MakeProfile | None].from_failure(target)
        return r[c.Infra.MakeProfile | None].ok(target.value.make_profile)


__all__: list[str] = ["FlextInfraCodegenLayoutGitignoreMixin"]
