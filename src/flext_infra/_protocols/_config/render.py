# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/render
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols._config import FlextInfraProtocolsConfigSonarcloud


class FlextInfraProtocolsConfigRender:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SonarcloudSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def exclusions(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            sonar.exclusions: generated, cache, vendored, and build output only;
            never governed source.
            """
            ...

        @property
        def cpd_exclusions(self) -> tuple[t.NonEmptyStr, ...]:
            """sonar.cpd.exclusions duplication-scope patterns."""
            ...

        @property
        def api_url(self) -> t.NonEmptyStr:
            """SonarCloud web API origin the settings sync writes to."""
            ...

        @property
        def api_timeout_seconds(self) -> t.PositiveInt:
            """Per-request SonarCloud web API timeout."""
            ...

        @property
        def issue_exclusions(
            self,
        ) -> tuple[
            FlextInfraProtocolsConfigSonarcloud.SonarcloudIssueExclusionSpec, ...
        ]:
            """Structural member projected from the owning model.

            Server-side issue exclusions applied through SonarCloud project
            settings; never written as file properties.
            """
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRender",
]
