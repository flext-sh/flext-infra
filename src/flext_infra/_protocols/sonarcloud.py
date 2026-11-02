# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/sonarcloud
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsSonarcloud:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class SonarcloudIssueFieldValue(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_key(self) -> t.NonEmptyStr: ...
        @property
        def resource_key(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class SonarcloudSetting(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def key(self) -> t.NonEmptyStr: ...
        @property
        def field_values(self) -> tuple[p.Infra.SonarcloudIssueFieldValue, ...]: ...

    @runtime_checkable
    class SonarcloudSettingsValues(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def settings(self) -> tuple[p.Infra.SonarcloudSetting, ...]: ...

    @runtime_checkable
    class SonarcloudAuthentication(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def valid(self) -> bool: ...

    @runtime_checkable
    class SonarcloudSettingsPlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def api_url(self) -> t.NonEmptyStr: ...
        @property
        def timeout_seconds(self) -> t.PositiveInt: ...
        @property
        def project_key(self) -> t.NonEmptyStr: ...
        @property
        def setting_key(self) -> t.NonEmptyStr: ...
        @property
        def field_values(self) -> tuple[p.Infra.SonarcloudIssueFieldValue, ...]: ...

    @runtime_checkable
    class SonarcloudSettingsWriteRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def api_path(self) -> t.NonEmptyStr: ...
        @property
        def form(self) -> tuple[tuple[str, str], ...]: ...

    @runtime_checkable
    class SonarcloudIssue(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def key(self) -> t.NonEmptyStr: ...
        @property
        def rule(self) -> t.NonEmptyStr: ...
        @property
        def component(self) -> t.NonEmptyStr: ...
        @property
        def line(self) -> int | None: ...
        @property
        def message(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class SonarcloudIssuePaging(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def page_index(self) -> t.PositiveInt: ...
        @property
        def page_size(self) -> t.PositiveInt: ...
        @property
        def total(self) -> int: ...

    @runtime_checkable
    class SonarcloudIssueSearch(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def paging(self) -> p.Infra.SonarcloudIssuePaging: ...
        @property
        def issues(self) -> tuple[p.Infra.SonarcloudIssue, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsSonarcloud",
]
