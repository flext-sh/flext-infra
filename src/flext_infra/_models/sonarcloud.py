"""Typed SonarCloud web API contracts for the server-side settings sync."""

from __future__ import annotations

from typing import Annotated, ClassVar

from flext_core import m
from flext_infra import t


class FlextInfraModelsSonarcloud:
    """Strict boundary models for the proven SonarCloud settings contract."""

    class SonarcloudIssueFieldValue(m.ContractModel):
        """One ``sonar.issue.ignore.multicriteria`` entry as the API spells it."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid", frozen=True, populate_by_name=True
        )

        rule_key: Annotated[
            t.NonEmptyStr,
            m.Field(
                validation_alias="ruleKey",
                serialization_alias="ruleKey",
                description="Sonar rule key",
            ),
        ]
        resource_key: Annotated[
            t.NonEmptyStr,
            m.Field(
                validation_alias="resourceKey",
                serialization_alias="resourceKey",
                description="Project-relative resource",
            ),
        ]

    class SonarcloudSetting(m.ContractModel):
        """One setting returned by ``api/settings/values``.

        The endpoint also reports bookkeeping (for example ``inherited``) that
        this contract does not consume; only ``key`` and ``fieldValues`` are
        read, so the unread keys are ignored rather than forbidden.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="ignore", frozen=True, populate_by_name=True
        )

        key: Annotated[t.NonEmptyStr, m.Field(description="Setting key")]
        field_values: Annotated[
            t.VariadicTuple[FlextInfraModelsSonarcloud.SonarcloudIssueFieldValue],
            m.Field(
                validation_alias="fieldValues",
                serialization_alias="fieldValues",
                description="PROPERTY_SET entries",
            ),
        ] = ()

    class SonarcloudSettingsValues(m.ContractModel):
        """The ``api/settings/values`` response body."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        settings: Annotated[
            t.VariadicTuple[FlextInfraModelsSonarcloud.SonarcloudSetting],
            m.Field(description="Settings the project defines for the asked keys"),
        ]

    class SonarcloudAuthentication(m.ContractModel):
        """The ``api/authentication/validate`` response body."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        valid: Annotated[bool, m.Field(description="Whether the token is valid")]

    class SonarcloudSettingsPlan(m.ContractModel):
        """The complete server-side state one project must carry, from the SSOT."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        api_url: Annotated[t.NonEmptyStr, m.Field(description="Web API origin")]
        timeout_seconds: Annotated[
            t.PositiveInt, m.Field(description="Per-request timeout")
        ]
        project_key: Annotated[
            t.NonEmptyStr, m.Field(description="<organization>_<repository>")
        ]
        setting_key: Annotated[
            t.NonEmptyStr, m.Field(description="PROPERTY_SET setting key")
        ]
        field_values: Annotated[
            t.VariadicTuple[FlextInfraModelsSonarcloud.SonarcloudIssueFieldValue],
            m.Field(min_length=1, description="Entries in SSOT order"),
        ]

        def current_field_values(
            self, current: FlextInfraModelsSonarcloud.SonarcloudSettingsValues
        ) -> t.VariadicTuple[FlextInfraModelsSonarcloud.SonarcloudIssueFieldValue]:
            """Return the entries the server holds for this plan's setting key."""
            return tuple(
                value
                for setting in current.settings
                if setting.key == self.setting_key
                for value in setting.field_values
            )

        def in_sync_with(
            self, current: FlextInfraModelsSonarcloud.SonarcloudSettingsValues
        ) -> bool:
            """Whether the server already holds exactly the SSOT entries.

            The property set is compared as a set: the API replaces the whole
            value, and the SSOT is validated duplicate-free, so order carries
            no meaning for which issues are excluded.
            """
            return frozenset(self.current_field_values(current)) == frozenset(
                self.field_values
            )

        def form_fields(self) -> t.VariadicTuple[t.Pair[str, str]]:
            """Return the ``api/settings/set`` form, one ``fieldValues`` per entry."""
            return (
                ("component", self.project_key),
                ("key", self.setting_key),
                *(
                    ("fieldValues", value.model_dump_json(by_alias=True))
                    for value in self.field_values
                ),
            )


__all__: list[str] = ["FlextInfraModelsSonarcloud"]
