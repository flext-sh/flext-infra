"""Declaration-only models for official gRPC compiler synchronization."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_cli import m
from flext_infra import p, t


class _GrpcCodegenModel(m.ContractModel):
    """Immutable base contract for one compiler synchronization record."""

    model_config: ClassVar[p.ConfigDict] = m.ConfigDict(
        extra="forbid", frozen=True, str_strip_whitespace=False
    )


# mro-wkii.17.26 (codex): models describe official protoc artifacts, never schemas.
class FlextInfraModelsCodegenGrpc:
    """Typed records for official protobuf and gRPC Python compiler artifacts."""

    class GrpcGeneratedArtifact(_GrpcCodegenModel):
        """One normalized compiler-owned Python file."""

        target: Path = m.Field(description="Live destination path.")
        content: str = m.Field(description="Canonical compiler source text.")

    class GrpcProjectRender(_GrpcCodegenModel):
        """Complete compiler artifact set for one project."""

        schemas: t.NonNegativeInt = m.Field(description="Compiled schema count.")
        artifacts: tuple[FlextInfraModelsCodegenGrpc.GrpcGeneratedArtifact, ...] = (
            m.Field(default=(), description="Ordered compiler-owned files.")
        )


__all__: list[str] = ["FlextInfraModelsCodegenGrpc"]
