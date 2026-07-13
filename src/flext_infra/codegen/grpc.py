"""Generate canonical Python gRPC modules from package-owned proto schemas."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, override

from flext_infra import c, r, t, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


# mro-wkii.17.26 (codex): compile real protobuf contracts; never synthesize .pyi.
class FlextInfraCodegenGrpc(s[bool]):
    """Synchronize ``*_pb2.py`` and ``*_pb2_grpc.py`` from package schemas."""

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
            f"gRPC codegen {mode}: {schemas} schema(s), {changed} changed module(s)"
        )
        if self.effective_dry_run and changed:
            return r[bool].fail(
                f"{changed} generated gRPC module(s) are stale; rerun with --apply"
            )
        return r[bool].ok(True)

    def _sync_project(self, project_root: Path) -> p.Result[t.Pair[int, int]]:
        """Generate and compare one project's package-owned proto schemas."""
        source_root = project_root / c.Infra.DEFAULT_SRC_DIR
        if not source_root.is_dir():
            return r[t.Pair[int, int]].ok((0, 0))
        proto_files = tuple(sorted(source_root.rglob(c.Infra.GRPC_PROTO_GLOB)))
        if not proto_files:
            return r[t.Pair[int, int]].ok((0, 0))
        with TemporaryDirectory(prefix="flext-grpc-codegen-") as temporary:
            generated_root = Path(temporary) / c.Infra.DEFAULT_SRC_DIR
            generated_root.mkdir(parents=True)
            command: t.StrSequence = (
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"--proto_path={source_root}",
                f"--python_out={generated_root}",
                f"--grpc_python_out={generated_root}",
                *(path.relative_to(source_root).as_posix() for path in proto_files),
            )
            generated = u.Cli.run(
                command, cwd=project_root, timeout=c.Infra.GRPC_CODEGEN_TIMEOUT_SECONDS
            )
            if generated.failure:
                return r[t.Pair[int, int]].fail(
                    generated.error or f"grpc_tools.protoc failed in {project_root}"
                )
            synchronized = self._sync_generated_modules(
                source_root=source_root,
                generated_root=generated_root,
                proto_files=proto_files,
            )
            if synchronized.failure:
                return r[t.Pair[int, int]].fail(
                    synchronized.error or f"cannot synchronize {project_root}"
                )
            return r[t.Pair[int, int]].ok((synchronized.value, len(proto_files)))

    def _sync_generated_modules(
        self,
        *,
        source_root: Path,
        generated_root: Path,
        proto_files: t.SequenceOf[Path],
    ) -> p.Result[int]:
        """Compare temporary compiler output and atomically update stale modules."""
        changed = 0
        for proto_file in proto_files:
            relative = proto_file.relative_to(source_root).with_suffix("")
            for suffix in c.Infra.GRPC_GENERATED_MODULE_SUFFIXES:
                relative_module = relative.parent / f"{relative.name}{suffix}"
                generated_path = generated_root / relative_module
                generated_read = u.Cli.files_read_text(generated_path)
                if generated_read.failure:
                    return r[int].fail(
                        generated_read.error
                        or f"compiler did not emit {generated_path}"
                    )
                target = source_root / relative_module
                current = u.Cli.files_read_text(target) if target.is_file() else None
                if current is not None and current.failure:
                    return r[int].fail(current.error or f"cannot read {target}")
                if current is not None and current.value == generated_read.value:
                    continue
                changed += 1
                relative_target = target.relative_to(source_root.parent)
                if self.effective_dry_run:
                    u.Cli.info(f"  stale: {relative_target}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                write = u.Cli.atomic_write_text_file(target, generated_read.value)
                if write.failure:
                    return r[int].fail(write.error or f"cannot write {target}")
                u.Cli.info(f"  generated: {relative_target}")
        return r[int].ok(changed)


__all__: list[str] = ["FlextInfraCodegenGrpc"]
