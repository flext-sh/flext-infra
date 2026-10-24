"""Gitignore ownership for the layout engine apply path.

Codegen-managed projects converge through the canonical conform render (one
owner, one template); unmanaged or external projects receive idempotent
appends of the missing patterns only.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenLayoutPlanMixin
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenLayoutGitignoreMixin:
    """Ensure the layout gitignore patterns for one project directory."""

    def _apply_gitignore(
        self,
        project_dir: Path,
        patterns: t.StrSequence,
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Ensure gitignore patterns via the canonical render or appending.

        Returns:
            The resulting ``p.Result[t.Infra.LayoutStatus]``.

        """
        project_dir = FlextInfraWorkspaceDetector.resolve_repository_root(
            project_dir,
        ).unwrap()
        inputs = u.Infra.load_codegen_inputs(project_dir).unwrap()
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            project_dir,
            inputs=inputs,
        ).unwrap()
        managed = self._managed_profile(project_dir, workspace, inputs=inputs)
        if managed.failure:
            return r[t.Infra.LayoutStatus].from_failure(managed)
        before = u.Cli.atomic_read_binary_file_state(
            project_dir / c.Infra.GITIGNORE,
            required=False,
        )
        if before.failure:
            return r[t.Infra.LayoutStatus].from_failure(before)
        current = (
            ""
            if before.value.content is None
            else before.value.content.decode(c.DEFAULT_ENCODING)
        )
        if managed.value is None:
            desired = self._gitignore_append_content(current, patterns)
        else:
            rendered = u.Infra.render_project_gitignore(
                inputs.spec,
                profile=managed.value,
                project_name=FlextInfraCodegenLayoutPlanMixin.layout_project_name(
                    project_dir,
                ),
                workspace=workspace,
                project_dir=project_dir,
            )
            if rendered.failure:
                return r[t.Infra.LayoutStatus].from_failure(rendered)
            desired = rendered.value
        if desired == current and before.value.mode == inputs.spec.modes.file_default:
            noop_status: t.Infra.LayoutStatus = "noop"
            return r[t.Infra.LayoutStatus].ok(noop_status)
        planned = m.Infra.CodegenFilePlan(
            project=project_dir,
            path=before.value.path,
            before=before.value,
            desired_content=desired.encode(c.DEFAULT_ENCODING),
            desired_mode=inputs.spec.modes.file_default,
            owner="codegen",
            policy="full" if managed.value is not None else "merge",
        )
        written = u.Infra.publish_codegen_plans(project_dir, (planned,))
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
    def _managed_profile(
        project_dir: Path,
        workspace: m.Infra.WorkspaceSpec,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[c.Infra.MakeProfile | None]:
        """Make profile when the project is governed by a workspace.

        Returns:
            The resulting ``p.Result[c.Infra.MakeProfile | None]``.

        """
        target = FlextInfraWorkspaceDetector.conform_target(
            project_dir,
            workspace,
            inputs=inputs,
        )
        if target.failure:
            return r[c.Infra.MakeProfile | None].from_failure(target)
        return r[c.Infra.MakeProfile | None].ok(target.value.make_profile)


__all__: list[str] = ["FlextInfraCodegenLayoutGitignoreMixin"]
