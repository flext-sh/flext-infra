"""Normalize and collect compiler-owned Python gRPC artifacts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config, m, p, r, t, u

if TYPE_CHECKING:
    from pathlib import Path


# mro-wkii.17.26 (codex): normalization never replaces protoc semantics.
class FlextInfraCodegenGrpcRenderMixin:
    """Format, validate, and read official ``grpc_tools.protoc`` outputs."""

    @staticmethod
    def _generated_module_paths(
        *, source_root: Path, generated_root: Path, proto_files: t.SequenceOf[Path]
    ) -> tuple[t.Pair[Path, Path], ...]:
        """Return temporary compiler modules paired with their live targets."""
        return tuple(
            (
                generated_root
                / proto_file.relative_to(source_root).parent
                / f"{proto_file.stem}{suffix}",
                source_root
                / proto_file.relative_to(source_root).parent
                / f"{proto_file.stem}{suffix}",
            )
            for proto_file in proto_files
            for suffix in c.Infra.GRPC_GENERATED_MODULE_SUFFIXES
        )

    @staticmethod
    def _normalize_compiler_outputs(
        module_paths: t.SequenceOf[t.Pair[Path, Path]], generated_root: Path
    ) -> p.Result[bool]:
        """Apply the declared safe normalization and prove compiler output clean."""
        generated_paths = tuple(generated for generated, _target in module_paths)
        missing = tuple(path for path in generated_paths if not path.is_file())
        if missing:
            return r[bool].fail(
                "grpc_tools.protoc omitted generated modules: "
                + ", ".join(str(path) for path in missing)
            )
        path_args = tuple(str(path) for path in generated_paths)
        commands: tuple[t.StrSequence, ...] = (
            (
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--isolated",
                "--no-cache",
                "--fix",
                "--select",
                ",".join(config.Infra.codegen.grpc.ruff_safe_fixes),
                *path_args,
            ),
            (c.Infra.RUFF, c.Infra.FORMAT, "--isolated", "--no-cache", *path_args),
            (
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--isolated",
                "--no-cache",
                "--no-fix",
                "--select",
                ",".join(config.Infra.codegen.grpc.ruff_safe_fixes),
                *path_args,
            ),
            (
                c.Infra.RUFF,
                c.Infra.FORMAT,
                "--isolated",
                "--no-cache",
                "--check",
                *path_args,
            ),
        )
        for command in commands:
            normalized = u.Cli.run(
                command,
                cwd=generated_root,
                timeout=c.Infra.GRPC_CODEGEN_TIMEOUT_SECONDS,
            )
            if normalized.failure:
                return r[bool].fail(
                    normalized.error or "generated gRPC module normalization failed"
                )
        for generated_path in generated_paths:
            source = u.Cli.files_read_text(generated_path)
            if source.failure:
                return r[bool].fail(
                    source.error or f"cannot read normalized module {generated_path}"
                )
            try:
                compile(source.value, str(generated_path), "exec")
            except SyntaxError as exc:
                return r[bool].fail(
                    f"normalized gRPC module is invalid: {generated_path}: {exc}"
                )
        return r[bool].ok(True)

    @classmethod
    def _compiler_artifacts(
        cls, *, source_root: Path, generated_root: Path, proto_files: t.SequenceOf[Path]
    ) -> p.Result[tuple[p.Infra.GrpcGeneratedArtifact, ...]]:
        """Return validated official compiler modules as synchronization artifacts."""
        module_paths = cls._generated_module_paths(
            source_root=source_root,
            generated_root=generated_root,
            proto_files=proto_files,
        )
        normalized = cls._normalize_compiler_outputs(module_paths, generated_root)
        if normalized.failure:
            return r[tuple[p.Infra.GrpcGeneratedArtifact, ...]].fail(normalized.error)
        artifacts: list[p.Infra.GrpcGeneratedArtifact] = []
        for generated_path, target in module_paths:
            source = u.Cli.files_read_text(generated_path)
            if source.failure:
                return r[tuple[p.Infra.GrpcGeneratedArtifact, ...]].fail(
                    source.error or f"cannot read compiler output {generated_path}"
                )
            artifacts.append(
                m.Infra.GrpcGeneratedArtifact(target=target, content=source.value)
            )
        return r[tuple[p.Infra.GrpcGeneratedArtifact, ...]].ok(tuple(artifacts))


__all__: list[str] = ["FlextInfraCodegenGrpcRenderMixin"]
