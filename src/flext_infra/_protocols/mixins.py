# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/mixins
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t


class FlextInfraProtocolsMixins:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModuleSelectionMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def module(self) -> str | None:
            """Structural member projected from the owning model.

            Dotted module path to scope verb to a single module (e.g.
            flext_core.result). Mutually compatible with --projects/--repository-
            root; narrows the run.
            """
            ...

    @runtime_checkable
    class NamespaceSelectionMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def namespace(self) -> str | None:
            """Structural member projected from the owning model.

            Alias namespace (c|m|p|t|u|r|e|h|s|x[.<Domain>]) to scope the verb to a
            single facade slot.
            """
            ...

    @runtime_checkable
    class ScopeMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository root."""
            ...

        @property
        def projects(self) -> Sequence[str] | None:
            """Projects to process; repeat --projects NAME as needed."""
            ...

        @property
        def verbose(self) -> bool:
            """Verbose output."""
            ...

    @runtime_checkable
    class ReadMixin(ScopeMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def report(self) -> str | None:
            """Output report file path."""
            ...

        @property
        def output_dir(self) -> str | None:
            """Output directory for reports."""
            ...

    @runtime_checkable
    class WriteMixin(ScopeMixin, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def apply(self) -> bool:
            """Apply changes instead of running in dry-run mode."""
            ...

        gates: Sequence[str]

        @property
        def dry_run(self) -> bool:
            """Whether writes are disabled (inverse of apply)."""
            ...

    @runtime_checkable
    class VersionTagMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> str:
            """Version string."""
            ...

        @property
        def tag(self) -> str:
            """Git tag (e.g. v1.0.0)."""
            ...

    @runtime_checkable
    class FilePathMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> t.NonEmptyStr:
            """File path."""
            ...

    @runtime_checkable
    class AbsoluteFilePathTextMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> t.NonEmptyStr:
            """Absolute file path."""
            ...

    @runtime_checkable
    class PositiveLineMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt:
            """Line number."""
            ...

    @runtime_checkable
    class RequiredNonNegativeLineMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.NonNegativeInt:
            """Line number."""
            ...

    @runtime_checkable
    class NonNegativeLineMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.NonNegativeInt:
            """Line number."""
            ...

    @runtime_checkable
    class NestedClassPathMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def class_path(self) -> str:
            """Nested class path."""
            ...

    @runtime_checkable
    class FileLineViolationMixin(FilePathMixin, PositiveLineMixin, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class CurrentImportMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def current_import(self) -> str:
            """Current import statement."""
            ...

    @runtime_checkable
    class ErrorDetailMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def detail(self) -> str:
            """Error detail."""
            ...

    @runtime_checkable
    class ProjectNameMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr:
            """Project name."""
            ...

    @runtime_checkable
    class ProjectEntryNameMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Project name."""
            ...

    @runtime_checkable
    class RepositoryRootPathMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository root path."""
            ...

    @runtime_checkable
    class ProjectNamesOptionalMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_names(self) -> Sequence[str] | None:
            """Project names."""
            ...

    @runtime_checkable
    class ProjectNamesListMixin(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        project_names: Sequence[str]


__all__: list[str] = [
    "FlextInfraProtocolsMixins",
]
