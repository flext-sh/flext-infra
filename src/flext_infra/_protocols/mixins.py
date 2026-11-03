# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/mixins
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsMixins:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModuleSelectionMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        module: str | None

    @runtime_checkable
    class NamespaceSelectionMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        namespace: str | None

    @runtime_checkable
    class ScopeMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path
        projects: Sequence[str] | None
        verbose: bool

    @runtime_checkable
    class ReadMixin(ScopeMixin, Protocol):
        """Structural data contract projected from the owning model."""

        report: str | None
        output_dir: str | None

    @runtime_checkable
    class WriteMixin(ScopeMixin, Protocol):
        """Structural data contract projected from the owning model."""

        apply: bool
        gates: Sequence[str]

        @property
        def dry_run(self) -> bool:
            """Whether writes are disabled (inverse of apply)."""
            ...

    @runtime_checkable
    class VersionTagMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        version: str
        tag: str

    @runtime_checkable
    class FilePathMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        file: t.NonEmptyStr

    @runtime_checkable
    class AbsoluteFilePathTextMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        file_path: t.NonEmptyStr

    @runtime_checkable
    class PositiveLineMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        line: t.PositiveInt

    @runtime_checkable
    class RequiredNonNegativeLineMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        line: t.NonNegativeInt

    @runtime_checkable
    class NonNegativeLineMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        line: t.NonNegativeInt

    @runtime_checkable
    class NestedClassPathMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        class_path: str

    @runtime_checkable
    class FileLineViolationMixin(FilePathMixin, PositiveLineMixin, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class CurrentImportMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        current_import: str

    @runtime_checkable
    class ErrorDetailMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        detail: str

    @runtime_checkable
    class ProjectNameMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        project: t.NonEmptyStr

    @runtime_checkable
    class ProjectEntryNameMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr

    @runtime_checkable
    class RepositoryRootPathMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path

    @runtime_checkable
    class ProjectNamesOptionalMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        project_names: Sequence[str] | None

    @runtime_checkable
    class ProjectNamesListMixin(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        project_names: Sequence[str]


__all__: list[str] = [
    "FlextInfraProtocolsMixins",
]
