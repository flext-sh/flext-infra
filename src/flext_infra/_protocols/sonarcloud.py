# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/sonarcloud
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t


class FlextInfraProtocolsSonarcloud:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SonarcloudIssueFieldValue(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_key(self) -> t.NonEmptyStr:
            """Sonar rule key."""
            ...

        @property
        def resource_key(self) -> t.NonEmptyStr:
            """Project-relative resource."""
            ...

    @runtime_checkable
    class SonarcloudSetting(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def key(self) -> t.NonEmptyStr:
            """Setting key."""
            ...

        @property
        def field_values(
            self,
        ) -> tuple[FlextInfraProtocolsSonarcloud.SonarcloudIssueFieldValue, ...]:
            """PROPERTY_SET entries."""
            ...

    @runtime_checkable
    class SonarcloudSettingsValues(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def settings(
            self,
        ) -> tuple[FlextInfraProtocolsSonarcloud.SonarcloudSetting, ...]:
            """Effective settings for the requested keys."""
            ...

    @runtime_checkable
    class SonarcloudAuthentication(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def valid(self) -> bool:
            """Whether the token is valid."""
            ...

    @runtime_checkable
    class SonarcloudSettingsPlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def api_url(self) -> t.NonEmptyStr:
            """Web API origin."""
            ...

        @property
        def timeout_seconds(self) -> t.PositiveInt:
            """Per-request timeout."""
            ...

        @property
        def project_key(self) -> t.NonEmptyStr:
            """<organization>_<repository>."""
            ...

        @property
        def setting_key(self) -> t.NonEmptyStr:
            """PROPERTY_SET setting key."""
            ...

        @property
        def field_values(
            self,
        ) -> tuple[FlextInfraProtocolsSonarcloud.SonarcloudIssueFieldValue, ...]:
            """Entries in SSOT order; empty means reset."""
            ...

    @runtime_checkable
    class SonarcloudSettingsWriteRequest(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def api_path(self) -> t.NonEmptyStr:
            """Web API endpoint."""
            ...

        @property
        def form(self) -> tuple[tuple[str, str], ...]:
            """Ordered form fields for the endpoint."""
            ...

    @runtime_checkable
    class SonarcloudIssue(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def key(self) -> t.NonEmptyStr:
            """Stable issue key."""
            ...

        @property
        def rule(self) -> t.NonEmptyStr:
            """Rule key."""
            ...

        @property
        def component(self) -> t.NonEmptyStr:
            """Project and file key."""
            ...

        @property
        def line(self) -> int | None:
            """Source line, when assigned."""
            ...

        @property
        def message(self) -> t.NonEmptyStr:
            """Observed finding."""
            ...

    @runtime_checkable
    class SonarcloudIssuePaging(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def page_index(self) -> t.PositiveInt:
            """One-based page index."""
            ...

        @property
        def page_size(self) -> t.PositiveInt:
            """Issues per page."""
            ...

        @property
        def total(self) -> int:
            """Total issues matching the server query."""
            ...

    @runtime_checkable
    class SonarcloudIssueSearch(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def paging(self) -> FlextInfraProtocolsSonarcloud.SonarcloudIssuePaging:
            """Server-side page accounting of this page."""
            ...

        @property
        def issues(self) -> tuple[FlextInfraProtocolsSonarcloud.SonarcloudIssue, ...]:
            """Issues returned on this page."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsSonarcloud",
]
