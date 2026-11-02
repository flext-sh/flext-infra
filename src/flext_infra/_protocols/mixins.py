# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import t


class FlextInfraProtocolsMixins:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ModuleSelectionMixin(Protocol):
        """Structural data contract projected from the owning model."""

        module: str | None = ...

    @runtime_checkable
    class NamespaceSelectionMixin(Protocol):
        """Structural data contract projected from the owning model."""

        namespace: str | None = ...

    @runtime_checkable
    class ScopeMixin(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path = ...
        projects: Sequence[str] | None = ...
        verbose: bool = ...

    @runtime_checkable
    class ReadMixin(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path = ...
        projects: Sequence[str] | None = ...
        verbose: bool = ...
        report: str | None = ...
        output_dir: str | None = ...

    @runtime_checkable
    class WriteMixin(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path = ...
        projects: Sequence[str] | None = ...
        verbose: bool = ...
        apply: bool = ...
        gates: Sequence[str] = ...

    @runtime_checkable
    class VersionTagMixin(Protocol):
        """Structural data contract projected from the owning model."""

        version: str = ...
        tag: str = ...

    @runtime_checkable
    class FilePathMixin(Protocol):
        """Structural data contract projected from the owning model."""

        file: t.NonEmptyStr

    @runtime_checkable
    class AbsoluteFilePathTextMixin(Protocol):
        """Structural data contract projected from the owning model."""

        file_path: t.NonEmptyStr

    @runtime_checkable
    class PositiveLineMixin(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.PositiveInt

    @runtime_checkable
    class RequiredNonNegativeLineMixin(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.NonNegativeInt

    @runtime_checkable
    class NonNegativeLineMixin(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.NonNegativeInt = ...

    @runtime_checkable
    class NestedClassPathMixin(Protocol):
        """Structural data contract projected from the owning model."""

        class_path: str = ...

    @runtime_checkable
    class FileLineViolationMixin(Protocol):
        """Structural data contract projected from the owning model."""

        line: t.PositiveInt
        file: t.NonEmptyStr

    @runtime_checkable
    class CurrentImportMixin(Protocol):
        """Structural data contract projected from the owning model."""

        current_import: str

    @runtime_checkable
    class ErrorDetailMixin(Protocol):
        """Structural data contract projected from the owning model."""

        detail: str = ...

    @runtime_checkable
    class ProjectNameMixin(Protocol):
        """Structural data contract projected from the owning model."""

        project: t.NonEmptyStr

    @runtime_checkable
    class ProjectEntryNameMixin(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr

    @runtime_checkable
    class RepositoryRootPathMixin(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path

    @runtime_checkable
    class ProjectNamesOptionalMixin(Protocol):
        """Structural data contract projected from the owning model."""

        project_names: Sequence[str] | None = ...

    @runtime_checkable
    class ProjectNamesListMixin(Protocol):
        """Structural data contract projected from the owning model."""

        project_names: Sequence[str] = ...


__all__: list[str] = [
    "FlextInfraProtocolsMixins",
]
