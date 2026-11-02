from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import p


from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra._constants.config import FlextInfraConstantsConfig

# Copyright (c) 2026 FLEXT Team. All rights reserved.
# SPDX-License-Identifier: MIT
"""Structural contracts mirrored from ``_models._config.workspace``.

This bootstrap contract lets the protocol projector construct the workspace
before it can publish the remaining model-module projections.
"""


class FlextInfraProtocolsConfigWorkspace:
    """Runtime-checkable contracts declared by the workspace model module."""

    @runtime_checkable
    class GitSubmoduleDeclaration(Protocol):
        """One declared Git submodule section."""

        @property
        def path(self) -> Path:
            """Path relative to the superproject root."""
            ...

        @property
        def url(self) -> str:
            """Declared upstream URL."""
            ...

        @property
        def branch(self) -> str:
            """Declared branch, when present."""
            ...

        @property
        def managed(self) -> bool | None:
            """Native participation flag."""
            ...

        @property
        def layer(self) -> FlextInfraConstantsConfig.MemberArchitectureLayer | None:
            """Optional architecture layer."""
            ...

    @runtime_checkable
    class DependencyGroupInclude(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def include_group(self) -> str:
            """Referenced dependency group."""
            ...

    @runtime_checkable
    class DependencyGroupDeclarations(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependency_groups(
            self,
        ) -> Mapping[str, tuple[str | p.Infra.DependencyGroupInclude, ...]]:
            """Ordered native dependency-group entries."""
            ...

    @runtime_checkable
    class DependencyManifestSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependency_groups(
            self,
        ) -> Mapping[str, tuple[str | p.Infra.DependencyGroupInclude, ...]]:
            """PEP 735 dependency groups declared by the member."""
            ...

        @property
        def name(self) -> str:
            """PEP 621 distribution name."""
            ...

        @property
        def dependencies(self) -> Sequence[str]:
            """PEP 621 runtime requirements."""
            ...

    @runtime_checkable
    class DependencyEdgeSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependent(self) -> str:
            """Member distribution declaring the requirement."""
            ...

        @property
        def dependency(self) -> str:
            """Member distribution it requires."""
            ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsConfigWorkspace",)
