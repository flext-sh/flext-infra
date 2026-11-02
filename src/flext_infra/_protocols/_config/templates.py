# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/templates
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigTemplates:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenVscodeSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def settings(self) -> t.Infra.SettingsPairs: ...
        @property
        def runtime_environment_token(self) -> t.NonEmptyStr | None: ...
        @property
        def map_union_settings(self) -> Mapping[str, t.JsonMapping]: ...
        @property
        def stripped_keys(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def stripped_map_keys(self) -> Mapping[str, tuple[str, ...]]: ...

    @runtime_checkable
    class CodegenVscodeDeclarationDelta(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def values(self) -> t.JsonMapping: ...

    @runtime_checkable
    class CodegenLayerProjection(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def values(self) -> t.JsonMapping: ...

    @runtime_checkable
    class ConfigDocumentInputs(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def values(self) -> t.JsonMapping: ...
        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class ManagedFileOwnership(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner(self) -> t.NonEmptyStr: ...
        @property
        def tracking(self) -> Literal["versioned", "runtime-local"]: ...
        @property
        def policy(self) -> Literal["full", "merge"]: ...
        @property
        def mode(self) -> int: ...
        @property
        def conflict_sections(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def preserve_project_keys(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def overwrite_project_keys(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def managed_tool_tables(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class TemplateDeclarationSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> Path | None: ...
        @property
        def source_kind(self) -> Literal["template", "resource"]: ...
        @property
        def source_package(self) -> t.NonEmptyStr | None: ...
        @property
        def source_closure(self) -> tuple[Path, ...]: ...
        @property
        def enforce(self) -> t.Infra.EnforcementIds: ...
        @property
        def requires_artifacts(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def profiles(self) -> tuple[c.Infra.MakeProfile, ...]: ...
        @property
        def ownership(self) -> p.Infra.ManagedFileOwnership | None: ...
        @property
        def requires_release_protocol(self) -> bool: ...
        @property
        def requires_beads(self) -> bool: ...
        @property
        def bootstrap_distribution(self) -> t.NonEmptyStr | None: ...

    @runtime_checkable
    class TemplateEntrySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> Path | None: ...
        @property
        def source_kind(self) -> Literal["template", "resource"]: ...
        @property
        def source_package(self) -> t.NonEmptyStr | None: ...
        @property
        def source_closure(self) -> tuple[Path, ...]: ...
        @property
        def enforce(self) -> t.Infra.EnforcementIds: ...
        @property
        def requires_artifacts(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def profiles(self) -> tuple[c.Infra.MakeProfile, ...]: ...
        @property
        def ownership(self) -> p.Infra.ManagedFileOwnership | None: ...
        @property
        def requires_release_protocol(self) -> bool: ...
        @property
        def requires_beads(self) -> bool: ...
        @property
        def bootstrap_distribution(self) -> t.NonEmptyStr | None: ...
        @property
        def destination(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class TemplatesSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path: ...
        @property
        def catalog(
            self,
        ) -> Mapping[t.NonEmptyStr, p.Infra.TemplateDeclarationSpec]: ...

    @runtime_checkable
    class ManagedFileSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner(self) -> t.NonEmptyStr: ...
        @property
        def tracking(self) -> Literal["versioned", "runtime-local"]: ...
        @property
        def policy(self) -> Literal["full", "merge"]: ...
        @property
        def mode(self) -> int: ...
        @property
        def conflict_sections(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def preserve_project_keys(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def overwrite_project_keys(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def managed_tool_tables(self) -> tuple[str, ...]: ...
        @property
        def path(self) -> Path: ...

    @runtime_checkable
    class GitignoreRenderContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def gitignore_sections(
            self,
        ) -> tuple[p.Infra.ScaffoldGitignoreSectionSpec, ...]: ...

    @runtime_checkable
    class GitignoreRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def gitignore_sections(
            self,
        ) -> tuple[p.Infra.ScaffoldGitignoreSectionSpec, ...]: ...

    @runtime_checkable
    class StaticTextRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""


__all__: list[str] = [
    "FlextInfraProtocolsConfigTemplates",
]
