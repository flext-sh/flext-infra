# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/transformers
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsTransformers:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SemanticPublicationOptions(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def validator(self) -> Callable[[Path], p.Result[bool]] | None: ...
        @property
        def plan_validator(
            self,
        ) -> Callable[[tuple[p.Cli.FileChange, ...]], p.Result[bool]] | None: ...
        @property
        def projection_roots(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class AliasMigrationContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def policy_owner(self) -> str: ...
        @property
        def import_root(self) -> str: ...

    @runtime_checkable
    class SemanticFilePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> Path: ...
        @property
        def path(self) -> Path: ...
        @property
        def before(self) -> p.Cli.AtomicFileState: ...
        @property
        def desired_content(self) -> bytes | None: ...
        @property
        def desired_mode(self) -> int | None: ...
        @property
        def changes(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class SemanticMigrationEdit(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path: ...
        @property
        def original_source(self) -> str | None: ...
        @property
        def updated_source(self) -> str: ...
        @property
        def retire_file(self) -> bool: ...
        @property
        def changes(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class SemanticBehaviorRewriteRequest(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        source: str
        modules: Mapping[str, tuple[str, bool]]
        ownership: tuple[
            Mapping[tuple[str, str], Sequence[tuple[str, str]]],
            frozenset[tuple[str, str, str, str]],
        ]
        utility_imports: frozenset[tuple[str, str]]
        declaration_imports: frozenset[tuple[str, str]]

    @runtime_checkable
    class DeclarationRelocationFinding(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path: ...
        @property
        def declaration(self) -> t.NonEmptyStr: ...
        @property
        def expected_owner(self) -> t.NonEmptyStr: ...
        @property
        def reason(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class CompatibilityAliasRewritePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def local_aliases(self) -> Mapping[str, str]: ...
        @property
        def import_aliases(self) -> Mapping[str, Mapping[str, str]]: ...
        @property
        def attribute_aliases(self) -> Mapping[tuple[str, str], str]: ...
        @property
        def qualified_aliases(self) -> Mapping[str, str]: ...
        @property
        def target_bindings(self) -> frozenset[str]: ...
        @property
        def preserved_reads(self) -> frozenset[tuple[int, int]]: ...
        @property
        def upstream_aliases(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class PrivateImportRewritePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def removals(self) -> Mapping[str, frozenset[str]]: ...
        @property
        def obsolete_imports(self) -> Mapping[str, frozenset[str]]: ...
        @property
        def replacements(self) -> Mapping[str, str]: ...
        @property
        def public_imports(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class Tier0ImportAnalysis(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package_name(self) -> str: ...
        @property
        def file_path(self) -> Path: ...
        @property
        def alias_to_module(self) -> Mapping[str, str]: ...
        @property
        def category_a(self) -> frozenset[str]: ...
        @property
        def category_b(self) -> frozenset[str]: ...
        @property
        def category_c(self) -> frozenset[str]: ...
        @property
        def category_d(self) -> frozenset[str]: ...
        @property
        def has_violations(self) -> bool: ...

    @runtime_checkable
    class SourceRewrite(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def start(self) -> int: ...
        @property
        def end(self) -> int: ...
        @property
        def text(self) -> str: ...

    @runtime_checkable
    class HeaderSpan(Protocol):
        """Structural data contract projected from the owning model."""

        shebang_end: int
        encoding_end: int
        comments_end: int
        docstring_end: int
        last_import_end: int

    @runtime_checkable
    class ClassBlockLayout(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def header_start(self) -> int: ...
        @property
        def header_end(self) -> int: ...
        @property
        def body_end(self) -> int: ...
        @property
        def indentation(self) -> int: ...
        @property
        def docstring_span(self) -> tuple[int, int] | None: ...

    @runtime_checkable
    class HeaderInfo(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def has_future_annotations(self) -> bool: ...
        @property
        def aliases(self) -> frozenset[str]: ...
        @property
        def span(self) -> p.Infra.HeaderSpan: ...

    @runtime_checkable
    class FacadeNamespaceCutover(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.Infra.RopeProject: ...
        @property
        def root(self) -> Path: ...
        @property
        def sources(self) -> Mapping[Path, str]: ...
        @property
        def working(self) -> MutableMapping[Path, str]: ...

    @runtime_checkable
    class FacadeNamespaceSite(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def source(self) -> str: ...
        @property
        def facade(self) -> ast.ClassDef: ...
        @property
        def namespace(self) -> ast.ClassDef: ...
        @property
        def children(self) -> tuple[ast.ClassDef, ...]: ...
        @property
        def tree(self) -> ast.Module: ...


__all__: list[str] = [
    "FlextInfraProtocolsTransformers",
]
