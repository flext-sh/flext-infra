# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/render
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsConfigRender:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SonarcloudSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def exclusions(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def cpd_exclusions(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def api_url(self) -> t.NonEmptyStr: ...
        @property
        def api_timeout_seconds(self) -> t.PositiveInt: ...
        @property
        def issue_exclusions(
            self,
        ) -> tuple[p.Infra.SonarcloudIssueExclusionSpec, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRender",
]
