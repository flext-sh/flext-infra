# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/layout
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols import FlextInfraProtocolsMiseToolchainBase

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsLayout:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class LayoutMoveSpec(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> t.NonEmptyStr:
            """Project-relative source."""
            ...

        @property
        def target(self) -> t.NonEmptyStr:
            """Project-relative target."""
            ...

    @runtime_checkable
    class LayoutProjectOverrideSpec(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def archive_names(self) -> tuple[t.NonEmptyStr, ...]:
            """Extra project-specific archived root entries."""
            ...

        @property
        def gitignore_additions(self) -> tuple[t.NonEmptyStr, ...]:
            """Patterns the project .gitignore must carry."""
            ...

        @property
        def moves(self) -> tuple[FlextInfraProtocolsLayout.LayoutMoveSpec, ...]:
            """Explicit nested source/target moves."""
            ...

        @property
        def archive_empty_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Directories archived once emptied by moves."""
            ...

        @property
        def keep_root_files(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Extra root files allowed to remain at project root (strict allowlist
            exceptions declared only here).
            """
            ...

        @property
        def ignore_globs(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Root entry name globs skipped entirely for this project (neither move
            nor review).
            """
            ...

    @runtime_checkable
    class LayoutSpec(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> int:
            """Config schema version."""
            ...

        @property
        def archive_root(self) -> t.NonEmptyStr:
            """Archive-not-delete root directory."""
            ...

        @property
        def docs_target(self) -> t.NonEmptyStr:
            """Canonical documentation directory."""
            ...

        @property
        def examples_target(self) -> t.NonEmptyStr:
            """Canonical examples directory."""
            ...

        @property
        def diagrams_target(self) -> t.NonEmptyStr:
            """Canonical diagrams directory."""
            ...

        @property
        def allow_hidden(self) -> bool:
            """Whether any `.*` root entry is canonical."""
            ...

        @property
        def canonical_root_files(self) -> tuple[t.NonEmptyStr, ...]:
            """Files allowed at the project root."""
            ...

        @property
        def canonical_root_dotfiles(self) -> tuple[t.NonEmptyStr, ...]:
            """Documented dotfiles allowed at the project root."""
            ...

        @property
        def canonical_root_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Directories allowed at the project root."""
            ...

        @property
        def profile_extra_root_files(self) -> Mapping[str, tuple[t.NonEmptyStr, ...]]:
            """Extra canonical root files per project profile."""
            ...

        @property
        def profile_project_patterns(self) -> Mapping[str, tuple[t.NonEmptyStr, ...]]:
            """Project-name globs resolving each profile."""
            ...

        @property
        def move_docs_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Root docs directories moved under docs_target."""
            ...

        @property
        def move_docs_files(self) -> tuple[t.NonEmptyStr, ...]:
            """Root Markdown files moved under docs_target."""
            ...

        @property
        def move_example_files(self) -> tuple[t.NonEmptyStr, ...]:
            """Sample data files moved under examples_target."""
            ...

        @property
        def move_diagram_globs(self) -> tuple[t.NonEmptyStr, ...]:
            """Root diagram globs moved under diagrams_target."""
            ...

        @property
        def archive_names(self) -> tuple[t.NonEmptyStr, ...]:
            """Root entries archived into archive_root."""
            ...

        @property
        def archive_globs(self) -> tuple[t.NonEmptyStr, ...]:
            """Root entry globs archived into archive_root."""
            ...

        @property
        def special_root_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Root directories skipped by the layout engine (e.g. content submodule
            trees under data/).
            """
            ...

        @property
        def reference_root_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            External reference corpora allowed at root (same class as
            docs/references; not product docs).
            """
            ...

        @property
        def project_overrides(
            self,
        ) -> Mapping[str, FlextInfraProtocolsLayout.LayoutProjectOverrideSpec]:
            """Per-project layout deltas keyed by project name."""
            ...

    @runtime_checkable
    class LayoutFinding(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule(self) -> t.Infra.LayoutRule:
            """Decision kind."""
            ...

        @property
        def path(self) -> t.NonEmptyStr:
            """Project-relative source path."""
            ...

        @property
        def target(self) -> str:
            """Project-relative destination path."""
            ...

        @property
        def message(self) -> t.NonEmptyStr:
            """Human-readable decision detail."""
            ...

        @property
        def status(self) -> t.Infra.LayoutStatus:
            """Execution status."""
            ...

    @runtime_checkable
    class LayoutProjectReport(
        FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr:
            """Project name."""
            ...

        @property
        def findings(self) -> tuple[FlextInfraProtocolsLayout.LayoutFinding, ...]:
            """All layout decisions for the project."""
            ...

        @property
        def actionable(self) -> tuple[FlextInfraProtocolsLayout.LayoutFinding, ...]:
            """Findings the engine acts on in apply mode (never review)."""
            ...

        @property
        def applied_count(self) -> int:
            """Number of findings executed by an apply run."""
            ...

    @runtime_checkable
    class LayoutRunReport(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def reports(self) -> tuple[FlextInfraProtocolsLayout.LayoutProjectReport, ...]:
            """Per-project layout outcomes."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsLayout",
]
