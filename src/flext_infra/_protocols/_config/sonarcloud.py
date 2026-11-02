# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/sonarcloud
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_cli import t


class FlextInfraProtocolsConfigSonarcloud:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SonarcloudIssueExclusionSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_key(self) -> t.NonEmptyStr: ...
        @property
        def resource_key(self) -> t.NonEmptyStr: ...
        @property
        def reason(self) -> t.NonEmptyStr: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigSonarcloud",
]
