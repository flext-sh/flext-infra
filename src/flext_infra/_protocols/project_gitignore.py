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
    class ProjectGitignorePreservedBlock(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def begin(self) -> t.NonEmptyStr:
            """Opening marker line."""
            ...

        @property
        def end(self) -> t.NonEmptyStr:
            """Closing marker line."""
            ...

    @runtime_checkable
    class ProjectGitignoreConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def patterns(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Ignore patterns appended, in declaration order, as one project-owned
            section of the generated .gitignore.
            """
            ...

        @property
        def preserved_blocks(
            self,
        ) -> tuple[
            FlextInfraProtocolsProjectGitignore.ProjectGitignorePreservedBlock, ...
        ]:
            """Structural member projected from the owning model.

            External generated blocks preserved from the live .gitignore; the
            external owner alone supplies their contents.
            """
            ...


__all__: list[str] = [
    "FlextInfraProtocolsProjectGitignore",
]
