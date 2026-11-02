# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/layout
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsLayout:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class LayoutMoveSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> t.NonEmptyStr: ...
        @property
        def target(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class LayoutProjectOverrideSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def archive_names(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def gitignore_additions(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def moves(self) -> tuple[p.Infra.LayoutMoveSpec, ...]: ...
        @property
        def archive_empty_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def keep_root_files(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def ignore_globs(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class LayoutSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> int: ...
        @property
        def archive_root(self) -> t.NonEmptyStr: ...
        @property
        def docs_target(self) -> t.NonEmptyStr: ...
        @property
        def examples_target(self) -> t.NonEmptyStr: ...
        @property
        def diagrams_target(self) -> t.NonEmptyStr: ...
        @property
        def allow_hidden(self) -> bool: ...
        @property
        def canonical_root_files(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def canonical_root_dotfiles(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def canonical_root_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def profile_extra_root_files(
            self,
        ) -> Mapping[str, tuple[t.NonEmptyStr, ...]]: ...
        @property
        def profile_project_patterns(
            self,
        ) -> Mapping[str, tuple[t.NonEmptyStr, ...]]: ...
        @property
        def move_docs_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def move_docs_files(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def move_example_files(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def move_diagram_globs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def archive_names(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def archive_globs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def special_root_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def reference_root_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def project_overrides(
            self,
        ) -> Mapping[str, p.Infra.LayoutProjectOverrideSpec]: ...

    @runtime_checkable
    class LayoutFinding(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule(self) -> t.Infra.LayoutRule: ...
        @property
        def path(self) -> t.NonEmptyStr: ...
        @property
        def target(self) -> str: ...
        @property
        def message(self) -> t.NonEmptyStr: ...
        @property
        def status(self) -> t.Infra.LayoutStatus: ...

    @runtime_checkable
    class LayoutProjectReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr: ...
        @property
        def findings(self) -> tuple[p.Infra.LayoutFinding, ...]: ...
        @property
        def actionable(self) -> tuple[p.Infra.LayoutFinding, ...]: ...
        @property
        def applied_count(self) -> int: ...

    @runtime_checkable
    class LayoutRunReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def reports(self) -> tuple[p.Infra.LayoutProjectReport, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsLayout",
]
