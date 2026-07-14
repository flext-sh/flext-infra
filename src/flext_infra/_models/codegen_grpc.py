"""Declaration-only models for descriptor-driven gRPC rendering."""

from __future__ import annotations

from typing import ClassVar, Literal

from flext_cli import m
from flext_infra import t


class _GrpcRenderModel(m.ContractModel):
    """Immutable base contract for one gRPC render record."""

    model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
        extra="forbid", frozen=True, str_strip_whitespace=False
    )


# mro-wkii.17.26 (codex): descriptors become typed data before Jinja rendering.
class FlextInfraModelsCodegenGrpc:
    """Typed render records for protobuf and gRPC Python modules."""

    class GrpcDependencyRender(_GrpcRenderModel):
        """One imported protobuf descriptor dependency."""

        module: t.NonEmptyStr = m.Field(description="Dependency module path.")
        alias: t.NonEmptyStr = m.Field(description="Private dependency import alias.")

    class GrpcFieldRender(_GrpcRenderModel):
        """One statically typed protobuf message field."""

        name: t.NonEmptyStr = m.Field(description="Python field name.")
        python_type: t.NonEmptyStr = m.Field(description="Public field annotation.")
        constructor_type: t.NonEmptyStr = m.Field(
            description="Keyword constructor annotation."
        )
        default_expression: t.NonEmptyStr = m.Field(
            description="Canonical constructor default expression."
        )

    class GrpcMessageRender(_GrpcRenderModel):
        """One generated protobuf message class."""

        name: t.NonEmptyStr = m.Field(description="Python message class name.")
        descriptor_name: t.NonEmptyStr = m.Field(
            description="Descriptor-local message name."
        )
        fields: tuple[FlextInfraModelsCodegenGrpc.GrpcFieldRender, ...] = m.Field(
            default=(), description="Ordered typed message fields."
        )

    class GrpcMethodRender(_GrpcRenderModel):
        """One gRPC method with separate Python and wire identities."""

        wire_name: t.NonEmptyStr = m.Field(description="Schema RPC name.")
        python_name: t.NonEmptyStr = m.Field(description="Snake-case Python name.")
        request_name: t.NonEmptyStr = m.Field(description="Request message class.")
        response_name: t.NonEmptyStr = m.Field(description="Response message class.")
        wire_path: t.NonEmptyStr = m.Field(description="Complete gRPC wire path.")
        cardinality: Literal["unary_unary"] = m.Field(
            description="Supported gRPC call cardinality."
        )

    class GrpcServiceRender(_GrpcRenderModel):
        """One protobuf service and its methods."""

        name: t.NonEmptyStr = m.Field(description="Python service name.")
        full_name: t.NonEmptyStr = m.Field(description="Wire service name.")
        registration_name: t.NonEmptyStr = m.Field(
            description="Snake-case server registration function name."
        )
        methods: tuple[FlextInfraModelsCodegenGrpc.GrpcMethodRender, ...] = m.Field(
            default=(), description="Ordered service methods."
        )

    class GrpcPb2RenderContext(_GrpcRenderModel):
        """Complete context for one generated ``*_pb2.py`` module."""

        source: t.NonEmptyStr = m.Field(description="Canonical proto source path.")
        module: t.NonEmptyStr = m.Field(description="Generated Python module path.")
        descriptor_hex_chunks: tuple[t.NonEmptyStr, ...] = m.Field(
            min_length=1, description="Serialized descriptor hexadecimal chunks."
        )
        third_party_dependencies: tuple[
            FlextInfraModelsCodegenGrpc.GrpcDependencyRender, ...
        ] = m.Field(default=(), description="Ordered third-party dependencies.")
        first_party_dependencies: tuple[
            FlextInfraModelsCodegenGrpc.GrpcDependencyRender, ...
        ] = m.Field(default=(), description="Ordered generated-package dependencies.")
        messages: tuple[FlextInfraModelsCodegenGrpc.GrpcMessageRender, ...] = m.Field(
            default=(), description="Ordered top-level messages."
        )
        exports: tuple[t.NonEmptyStr, ...] = m.Field(
            default=(), description="Ordered public module exports."
        )
        needs_mapping: bool = m.Field(
            default=False, description="Render the Mapping type import."
        )
        needs_sequence: bool = m.Field(
            default=False, description="Render the Sequence type import."
        )

    class GrpcPb2GrpcRenderContext(_GrpcRenderModel):
        """Complete context for one generated ``*_pb2_grpc.py`` module."""

        source: t.NonEmptyStr = m.Field(description="Canonical proto source path.")
        pb2_module: t.NonEmptyStr = m.Field(description="Sibling pb2 module path.")
        services: tuple[FlextInfraModelsCodegenGrpc.GrpcServiceRender, ...] = m.Field(
            default=(), description="Ordered protobuf services."
        )
        exports: tuple[t.NonEmptyStr, ...] = m.Field(
            default=(), description="Ordered public module exports."
        )


__all__: list[str] = ["FlextInfraModelsCodegenGrpc"]
