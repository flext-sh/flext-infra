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

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import t


class FlextInfraProtocolsTransformers:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SemanticPublicationOptions(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Original observations required by every publication effect."""
            ...

        @property
        def validator(self) -> Callable[[Path], p.Result[bool]] | None:
            """Consumer acceptance gate over the previewed view root."""
            ...

        @property
        def plan_validator(
            self,
        ) -> Callable[[tuple[p.Cli.FileChange, ...]], p.Result[bool]] | None:
            """Structural member projected from the owning model.

            Consumer acceptance gate over the normalized candidate changes, for a
            consumer that reads its own snapshot instead of a view root.
            """
            ...

        @property
        def projection_roots(self) -> tuple[Path, ...]:
            """Generated projection roots composed into the publication."""
            ...

    @runtime_checkable
    class AliasMigrationContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def policy_owner(self) -> str:
            """Project package that owns the canonical alias policy."""
            ...

        @property
        def import_root(self) -> str:
            """Public facade root from which consumers import."""
            ...

    @runtime_checkable
    class SemanticFilePlan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> Path:
            """Physical owning project root."""
            ...

        @property
        def path(self) -> Path:
            """Absolute managed file path."""
            ...

        @property
        def before(self) -> p.Cli.AtomicFileState:
            """Descriptor-authenticated file state before migration."""
            ...

        @property
        def desired_content(self) -> bytes | None:
            """Exact desired bytes after migration, or None for no change."""
            ...

        @property
        def desired_mode(self) -> int | None:
            """Exact desired mode, or None for no change."""
            ...

        @property
        def changes(self) -> tuple[str, ...]:
            """Recorded migration operations."""
            ...

    @runtime_checkable
    class SemanticMigrationEdit(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path:
            """Source file to rewrite."""
            ...

        @property
        def original_source(self) -> str | None:
            """Structural member projected from the owning model.

            Source bytes before migration; None declares a creation whose
            destination must not exist when published.
            """
            ...

        @property
        def updated_source(self) -> str:
            """Prospective source bytes after migration."""
            ...

        @property
        def retire_file(self) -> bool:
            """Explicit source retirement, not empty-file output."""
            ...

        @property
        def changes(self) -> tuple[str, ...]:
            """Recorded migration operations."""
            ...

    @runtime_checkable
    class SemanticBehaviorRewriteRequest(FlextCliProtocols.BaseModel, Protocol):
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
    class DeclarationRelocationFinding(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path:
            """Source file declaring the unrelocated payload."""
            ...

        @property
        def declaration(self) -> t.NonEmptyStr:
            """Qualified ``Outer.Payload`` declaration name."""
            ...

        @property
        def expected_owner(self) -> t.NonEmptyStr:
            """Owner the relocation expected to resolve."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Why that owner did not resolve."""
            ...

    @runtime_checkable
    class CompatibilityAliasRewritePlan(
        FlextInfraProtocolsBase.FrozenArbitrary, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def local_aliases(self) -> Mapping[str, str]:
            """Aliases the file declares, mapped to their targets."""
            ...

        @property
        def import_aliases(self) -> Mapping[str, Mapping[str, str]]:
            """Imported aliases per source module and their targets."""
            ...

        @property
        def attribute_aliases(self) -> Mapping[tuple[str, str], str]:
            """Module attribute alias accesses and their targets."""
            ...

        @property
        def qualified_aliases(self) -> Mapping[str, str]:
            """Qualified alias identities mapped to their targets."""
            ...

        @property
        def target_bindings(self) -> frozenset[str]:
            """Module-level names the file already binds."""
            ...

        @property
        def preserved_reads(self) -> frozenset[tuple[int, int]]:
            """Eager upstream reads before a local alias rebind."""
            ...

        @property
        def upstream_aliases(self) -> Mapping[str, str]:
            """Proven upstream identities preceding local aliases."""
            ...

        @property
        def root_published_modules(self) -> frozenset[str]:
            """Service modules whose aliases the package root publishes."""
            ...

    @runtime_checkable
    class PrivateImportRewritePlan(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def removals(self) -> Mapping[str, frozenset[str]]:
            """Private symbols removed per source module."""
            ...

        @property
        def obsolete_imports(self) -> Mapping[str, frozenset[str]]:
            """Public roots superseded by their facade alias."""
            ...

        @property
        def replacements(self) -> Mapping[str, str]:
            """Private qualified identities and public references."""
            ...

        @property
        def public_imports(self) -> Mapping[str, str]:
            """Facade aliases mapped to their publishing package."""
            ...

    @runtime_checkable
    class Tier0ImportAnalysis(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package_name(self) -> str:
            """Resolved package name for the analyzed file."""
            ...

        @property
        def file_path(self) -> Path:
            """Python file analyzed for Tier 0 import violations."""
            ...

        @property
        def alias_to_module(self) -> Mapping[str, str]:
            """Alias names mapped to their source modules."""
            ...

        @property
        def category_a(self) -> frozenset[str]:
            """Top-level aliases that are informational only."""
            ...

        @property
        def category_b(self) -> frozenset[str]:
            """Core aliases to redirect to the core package."""
            ...

        @property
        def category_c(self) -> frozenset[str]:
            """Aliases to move into a TYPE_CHECKING block."""
            ...

        @property
        def category_d(self) -> frozenset[str]:
            """Runtime-used aliases requiring direct import handling."""
            ...

        @property
        def has_violations(self) -> bool:
            """True if any imports need redirecting or moving."""
            ...

    @runtime_checkable
    class SourceRewrite(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def start(self) -> int:
            """Start byte offset in the source."""
            ...

        @property
        def end(self) -> int:
            """End byte offset in the source."""
            ...

        @property
        def text(self) -> str:
            """Replacement text."""
            ...

    @runtime_checkable
    class HeaderSpan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        shebang_end: int
        encoding_end: int
        comments_end: int
        docstring_end: int
        last_import_end: int

    @runtime_checkable
    class ClassBlockLayout(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def header_start(self) -> int:
            """First header line."""
            ...

        @property
        def header_end(self) -> int:
            """Last header line."""
            ...

        @property
        def body_end(self) -> int:
            """Last body line."""
            ...

        @property
        def indentation(self) -> int:
            """Body indent width stripped per line."""
            ...

        @property
        def docstring_span(self) -> tuple[int, int] | None:
            """Wrapper docstring line span."""
            ...

    @runtime_checkable
    class HeaderInfo(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def has_future_annotations(self) -> bool:
            """Whether the module already imports annotations."""
            ...

        @property
        def aliases(self) -> frozenset[str]:
            """Local names bound by from-import statements."""
            ...

        @property
        def span(self) -> FlextInfraProtocolsTransformers.HeaderSpan:
            """Byte offsets for the header sections."""
            ...

    @runtime_checkable
    class FacadeNamespaceCutover(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.Infra.RopeProject:
            """Rope project snapshot holding the editable sources."""
            ...

        @property
        def root(self) -> Path:
            """Physical project root."""
            ...

        @property
        def sources(self) -> Mapping[Path, str]:
            """Editable source bytes per path."""
            ...

        @property
        def working(self) -> MutableMapping[Path, str]:
            """Prospective source bytes per path."""
            ...

    @runtime_checkable
    class FacadeNamespaceSite(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Source path holding the facade."""
            ...

        @property
        def source(self) -> str:
            """Source bytes holding the facade."""
            ...

        @property
        def facade(self) -> ast.ClassDef:
            """Facade composition class."""
            ...

        @property
        def namespace(self) -> ast.ClassDef:
            """Single composed namespace class."""
            ...

        @property
        def children(self) -> tuple[ast.ClassDef, ...]:
            """Facade body classes."""
            ...

        @property
        def tree(self) -> ast.Module:
            """Parsed source module."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsTransformers",
]
