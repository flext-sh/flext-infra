"""Compile canonical Python gRPC modules with ``grpc_tools.protoc``."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen._grpc.render import FlextInfraCodegenGrpcRenderMixin


# mro-wkii.17.26 (codex): protoc exclusively owns protobuf and gRPC semantics.
class FlextInfraCodegenGrpcEngineMixin(FlextInfraCodegenGrpcRenderMixin):
    """Compile and collect official Python artifacts for every owned schema."""

    @classmethod
    def _generate_project(
        cls, project_root: Path
    ) -> p.Result[p.Infra.GrpcProjectRender]:
        """Compile every package-owned schema into normalized temporary modules."""
        source_root = project_root / c.Infra.DEFAULT_SRC_DIR
        if not source_root.is_dir():
            return r[p.Infra.GrpcProjectRender].ok(m.Infra.GrpcProjectRender(schemas=0))
        proto_files = tuple(sorted(source_root.rglob(c.Infra.GRPC_PROTO_GLOB)))
        if not proto_files:
            return r[p.Infra.GrpcProjectRender].ok(m.Infra.GrpcProjectRender(schemas=0))
        source_names = tuple(
            path.relative_to(source_root).as_posix() for path in proto_files
        )
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
                *source_names,
            )
            compiled = u.Cli.run(
                command, cwd=project_root, timeout=c.Infra.GRPC_CODEGEN_TIMEOUT_SECONDS
            )
            if compiled.failure:
                return r[p.Infra.GrpcProjectRender].fail(
                    compiled.error or f"grpc_tools.protoc failed in {project_root}"
                )
            artifacts = cls._compiler_artifacts(
                source_root=source_root,
                generated_root=generated_root,
                proto_files=proto_files,
            )
            if artifacts.failure:
                return r[p.Infra.GrpcProjectRender].fail(artifacts.error)
            return r[p.Infra.GrpcProjectRender].ok(
                m.Infra.GrpcProjectRender(
                    schemas=len(proto_files), artifacts=artifacts.value
                )
            )


__all__: list[str] = ["FlextInfraCodegenGrpcEngineMixin"]
