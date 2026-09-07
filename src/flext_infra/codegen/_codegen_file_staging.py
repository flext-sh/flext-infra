"""Destination-local staging for ordinary managed codegen files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenFileStaging:
    """Authenticate and stage every non-Mise file before live publication."""

    @classmethod
    def stage(
        cls,
        workspace: m.Infra.MiseToolchainWorkspacePlan,
        plans: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> p.Result[tuple[m.Cli.AtomicFilePublication, ...]]:
        """Build guarded publications without changing a live destination."""
        result_type = r[tuple[m.Cli.AtomicFilePublication, ...]]
        paths = tuple(plan.path.absolute() for plan in plans)
        if len(set(paths)) != len(paths):
            return result_type.fail("duplicate managed codegen publication path")
        mise_paths = {
            artifact
            for project in workspace.projects
            for artifact in (
                project.layout.artifacts.config,
                project.layout.artifacts.unix_launcher,
                project.layout.artifacts.windows_launcher,
                project.layout.artifacts.lock,
            )
        }
        publications: list[m.Cli.AtomicFilePublication] = []
        for plan in plans:
            if plan.path.absolute() in mise_paths:
                return result_type.fail(
                    f"ordinary codegen plan duplicates Mise ownership: {plan.path}"
                )
            publication = cls._stage_one(workspace.layout, plan)
            if publication.failure:
                return result_type.from_failure(publication)
            publications.append(publication.value)
        return result_type.ok(tuple(publications))

    @staticmethod
    def _stage_one(
        layout: m.Infra.MiseToolchainWorkspaceLayout, plan: m.Infra.CodegenFilePlan
    ) -> p.Result[m.Cli.AtomicFilePublication]:
        """Authenticate one plan and materialize its destination-local candidate."""
        result_type = r[m.Cli.AtomicFilePublication]
        if not u.Infra.codegen_file_requires_effect(plan):
            return result_type.fail(f"invalid changed codegen plan: {plan.path}")
        target = plan.path.absolute()
        owner = next(
            (
                project
                for project in layout.projects
                if target.is_relative_to(project.root.absolute())
            ),
            None,
        )
        if owner is None:
            return result_type.fail(
                f"managed codegen plan escapes its project: {target}"
            )
        before = u.Cli.atomic_read_binary_file_state(target, required=False)
        if before.failure:
            return result_type.from_failure(before)
        current_digest = (
            ""
            if before.value.content is None
            else u.Cli.sha256_bytes(before.value.content)
        )
        planned_digest = (
            ""
            if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
            or plan.before.content is None
            else u.Cli.sha256_bytes(plan.before.content)
        )
        if current_digest != planned_digest:
            return result_type.fail(f"managed file changed after planning: {target}")
        relative = target.relative_to(owner.root.absolute())
        if owner.transaction_root is None:
            return result_type.fail(
                f"managed codegen stage has no transaction root: {target}"
            )
        staged_path = owner.transaction_root / "managed" / relative
        try:
            staged_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return result_type.fail_op(
                f"create managed codegen stage for {target}", exc
            )
        if plan.desired_content is None:
            replacement = u.Cli.atomic_read_binary_file_state(
                staged_path, required=False
            )
        else:
            content = plan.desired_content
            mode = before.value.mode or 0o644
            if plan.desired_mode is not None:
                mode = plan.desired_mode
            written = u.Cli.atomic_create_binary_file_guarded(
                staged_path, content, permission_mode=mode
            )
            if written.failure:
                return result_type.from_failure(written)
            replacement = u.Cli.atomic_read_binary_file_state(
                staged_path, required=True
            )
        if replacement.failure:
            return result_type.from_failure(replacement)
        return result_type.ok(
            m.Cli.AtomicFilePublication(
                before=before.value, replacement=replacement.value
            )
        )


__all__: list[str] = ["FlextInfraCodegenFileStaging"]
