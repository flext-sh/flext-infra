"""Generate canonical Python gRPC modules from package-owned proto schemas."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import r, t, u
from flext_infra.base import s
from flext_infra.codegen._grpc.engine import FlextInfraCodegenGrpcEngineMixin

if TYPE_CHECKING:
    from flext_infra import p


# mro-wkii.17.26 (codex): thin facade applies only validated compiler artifacts.
class FlextInfraCodegenGrpc(FlextInfraCodegenGrpcEngineMixin, s[bool]):
    """Synchronize official gRPC compiler modules across selected projects."""

    @override
    def execute(self) -> p.Result[bool]:
        """Generate or verify every discovered project's gRPC modules."""
        projects_result = u.Infra.projects(self.workspace_root)
        if projects_result.failure:
            return r[bool].fail(
                projects_result.error or "gRPC project discovery failed"
            )
        selected = (
            frozenset(self.project_filter.split(","))
            if self.project_filter
            else frozenset()
        )
        changed = 0
        schemas = 0
        for project in projects_result.value:
            if (
                selected
                and project.name not in selected
                and project.path.name not in selected
            ):
                continue
            project_result = self._sync_project(project.path)
            if project_result.failure:
                return r[bool].fail(
                    project_result.error or f"gRPC generation failed for {project.path}"
                )
            project_changed, project_schemas = project_result.value
            changed += project_changed
            schemas += project_schemas
        mode = "check" if self.effective_dry_run else "apply"
        u.Cli.info(
            f"gRPC codegen {mode}: {schemas} schema(s), {changed} changed artifact(s)"
        )
        if self.effective_dry_run and changed:
            return r[bool].fail(
                f"{changed} generated gRPC artifact(s) are stale; rerun with --apply"
            )
        return r[bool].ok(True)

    def _sync_project(self, project_root: Path) -> p.Result[t.Pair[int, int]]:
        """Compile and synchronize one project's complete generated artifact set."""
        generated = self._generate_project(project_root)
        if generated.failure:
            return r[t.Pair[int, int]].fail(
                generated.error or f"cannot generate gRPC artifacts for {project_root}"
            )
        changed = 0
        for artifact in generated.value.artifacts:
            current = (
                u.Cli.files_read_text(artifact.target)
                if artifact.target.is_file()
                else None
            )
            if current is not None and current.failure:
                return r[t.Pair[int, int]].fail(
                    current.error or f"cannot read {artifact.target}"
                )
            if current is not None and current.value == artifact.content:
                continue
            changed += 1
            relative_target = artifact.target.relative_to(project_root)
            if self.effective_dry_run:
                u.Cli.info(f"  stale: {relative_target}")
                continue
            written = u.Cli.atomic_write_text_file(artifact.target, artifact.content)
            if written.failure:
                return r[t.Pair[int, int]].fail(
                    written.error or f"cannot write {artifact.target}"
                )
            u.Cli.info(f"  generated: {relative_target}")
        return r[t.Pair[int, int]].ok((changed, generated.value.schemas))


__all__: list[str] = ["FlextInfraCodegenGrpc"]
