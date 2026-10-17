"""Gitignore ownership for the layout engine apply path.

Codegen-managed projects converge through the canonical conform render (one
owner, one template); unmanaged or external projects receive idempotent
appends of the missing patterns only.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from flext_infra import c, m, p, r, t, u
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
        project_dir = FlextInfraWorkspaceDetector.resolve_repository_root(
            project_dir,
        ).unwrap()
        inputs = u.Infra.load_codegen_inputs(project_dir).unwrap()
        topology = u.Cli.atomic_read_binary_file_state(
            project_dir / c.Infra.GITMODULES,
            required=False,
        ).unwrap()
        source_states = (*inputs.sources, topology)
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            project_dir,
            inputs=inputs,
        ).unwrap()
        managed = self._managed_profile(project_dir, workspace, inputs=inputs)
        if managed.failure:
            return r[t.Infra.LayoutStatus].from_failure(managed)
        profile = managed.value
        if profile is not None:
            return self._apply_gitignore_managed(project_dir, profile)
        return self._apply_gitignore_append(project_dir, patterns)

    @classmethod
    def _apply_gitignore_managed(
        cls,
        project_dir: Path,
        profile: c.Infra.MakeProfile,
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Write the canonical rendered gitignore for a governed project.

        Returns:
            The resulting ``p.Result[t.Infra.LayoutStatus]``.

        """
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
        return cls._converge_gitignore(
            project_dir, "full", lambda _current: rendered.value
        )

    @classmethod
    def _apply_gitignore_append(
        cls,
        project_dir: Path,
        patterns: t.StrSequence,
    ) -> str:
        """Derive missing layout patterns from the captured gitignore text.

        Returns:
            The original text or its extension with the missing patterns.

        """

        def appended(current: str) -> str:
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
            return text + "\n".join(missing) + "\n"

        return cls._converge_gitignore(project_dir, "merge", appended)

    @staticmethod
    def _converge_gitignore(
        project_dir: Path,
        policy: Literal["full", "merge"],
        desired: Callable[[str], str],
    ) -> p.Result[t.Infra.LayoutStatus]:
        """Publish the desired gitignore text when it differs from the current one.

        Returns:
            ``noop`` when the file already holds the desired text, else ``applied``.

        """
        gitignore_path = project_dir / c.Infra.GITIGNORE
        current = ""
        if gitignore_path.is_file():
            read = u.Cli.files_read_text(gitignore_path)
            if read.failure:
                return r[t.Infra.LayoutStatus].from_failure(read)
            current = read.value
        text = desired(current)
        if text == current:
            noop_status: t.Infra.LayoutStatus = "noop"
            return r[t.Infra.LayoutStatus].ok(noop_status)
        before = u.Cli.atomic_read_binary_file_state(gitignore_path, required=False)
        if before.failure:
            return r[t.Infra.LayoutStatus].from_failure(before)
        written = FlextInfraMisePublication.publish_file_plan(
            m.Infra.CodegenFilePlan(
                project=project_dir,
                path=gitignore_path,
                before=before.value,
                desired_content=text.encode(c.DEFAULT_ENCODING),
                desired_mode=config.Infra.codegen.modes.file_default,
                owner="codegen",
                policy=policy,
            ),
            phase=c.Infra.CodegenStagedFilePhase.LAYOUT,
        )
        if written.failure:
            return r[t.Infra.LayoutStatus].from_failure(written)
        applied_status: t.Infra.LayoutStatus = "applied"
        return r[t.Infra.LayoutStatus].ok(applied_status)

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
