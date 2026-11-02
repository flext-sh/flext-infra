# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsSonarcloud:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class SonarcloudIssueFieldValue(Protocol):
        """Structural data contract projected from the owning model."""

        rule_key: t.NonEmptyStr
        resource_key: t.NonEmptyStr

    @runtime_checkable
    class SonarcloudSettingsValues(Protocol):
        """Structural data contract projected from the owning model."""

        settings: tuple[FlextInfraProtocolsSonarcloud.SonarcloudSetting, ...]

    @runtime_checkable
    class SonarcloudAuthentication(Protocol):
        """Structural data contract projected from the owning model."""

        valid: bool

    @runtime_checkable
    class SonarcloudSettingsPlan(Protocol):
        """Structural data contract projected from the owning model."""

        api_url: t.NonEmptyStr
        timeout_seconds: t.PositiveInt
        project_key: t.NonEmptyStr
        setting_key: t.NonEmptyStr
        field_values: tuple[
            FlextInfraProtocolsSonarcloud.SonarcloudIssueFieldValue, ...
        ]

    @runtime_checkable
    class SonarcloudSettingsWriteRequest(Protocol):
        """Structural data contract projected from the owning model."""

        api_path: t.NonEmptyStr
        form: tuple[tuple[str, str], ...]


__all__: list[str] = [
    "FlextInfraProtocolsSonarcloud",
]
