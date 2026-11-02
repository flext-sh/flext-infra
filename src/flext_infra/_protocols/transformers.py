# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsTransformers:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class AliasMigrationContext(Protocol):
        """Structural data contract projected from the owning model."""

        policy_owner: str
        import_root: str

    @runtime_checkable
    class SemanticFilePlan(Protocol):
        """Structural data contract projected from the owning model."""

        project: Path
        path: Path
        before: m.Cli.AtomicFileState
        desired_content: bytes | None
        desired_mode: int | None
        changes: tuple[str, ...] = ...

    @runtime_checkable
    class SemanticMigrationEdit(Protocol):
        """Structural data contract projected from the owning model."""

        file_path: Path
        original_source: str | None
        updated_source: str
        retire_file: bool = ...
        changes: tuple[str, ...] = ...

    @runtime_checkable
    class DeclarationRelocationFinding(Protocol):
        """Structural data contract projected from the owning model."""

        file_path: Path
        declaration: t.NonEmptyStr
        expected_owner: t.NonEmptyStr
        reason: t.NonEmptyStr

    @runtime_checkable
    class CompatibilityAliasRewritePlan(Protocol):
        """Structural data contract projected from the owning model."""

        local_aliases: Mapping[str, str]
        import_aliases: Mapping[str, Mapping[str, str]]
        attribute_aliases: Mapping[tuple[str, str], str]
        qualified_aliases: Mapping[str, str]
        target_bindings: frozenset[str]
        preserved_reads: frozenset[tuple[int, int]] = ...
        upstream_aliases: Mapping[str, str] = ...

    @runtime_checkable
    class PrivateImportRewritePlan(Protocol):
        """Structural data contract projected from the owning model."""

        removals: Mapping[str, frozenset[str]]
        obsolete_imports: Mapping[str, frozenset[str]]
        replacements: Mapping[str, str]
        public_imports: Mapping[str, str]

    @runtime_checkable
    class SourceRewrite(Protocol):
        """Structural data contract projected from the owning model."""

        start: int
        end: int
        text: str

    @runtime_checkable
    class HeaderInfo(Protocol):
        """Structural data contract projected from the owning model."""

        has_future_annotations: bool
        aliases: frozenset[str]
        span: FlextInfraModelsTransformers.HeaderSpan

    @runtime_checkable
    class FacadeNamespaceSite(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        source: str
        facade: t.Port[ast.ClassDef]
        namespace: t.Port[ast.ClassDef]
        children: tuple[t.Port[ast.ClassDef], ...]
        tree: t.Port[ast.Module]


__all__: list[str] = [
    "FlextInfraProtocolsTransformers",
]
