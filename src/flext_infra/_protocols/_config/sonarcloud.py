# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/sonarcloud
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsConfigSonarcloud:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SonarcloudIssueExclusionSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def rule_key(self) -> t.NonEmptyStr:
            """Sonar rule key, e.g. 'text:S8565'."""
            ...

        @property
        def resource_key(self) -> t.NonEmptyStr:
            """Project-relative resource pattern."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Operator justification and bead."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigSonarcloud",
]
