# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/project_gitignore
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsProjectGitignore:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectGitignorePreservedBlock(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        begin: t.NonEmptyStr
        end: t.NonEmptyStr

    @runtime_checkable
    class ProjectGitignoreConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        patterns: tuple[t.NonEmptyStr, ...]
        preserved_blocks: tuple[
            FlextInfraProtocolsProjectGitignore.ProjectGitignorePreservedBlock, ...
        ]


__all__: list[str] = [
    "FlextInfraProtocolsProjectGitignore",
]
