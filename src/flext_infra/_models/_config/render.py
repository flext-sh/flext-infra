"""Declarative SonarCloud policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m, t

from flext_infra._models._config.contract import FlextInfraModelsConfigContract
from flext_infra._models._config.sonarcloud import FlextInfraModelsConfigSonarcloud


class FlextInfraModelsConfigRender(FlextInfraModelsConfigSonarcloud):
    """Policy declarations consumed by the configuration contract."""

    class SonarcloudSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Fleet SonarCloud automatic-analysis scope policy."""

        exclusions: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description=(
                    "sonar.exclusions: generated, cache, vendored, and build "
                    "output only; never governed source"
                ),
            ),
        ]
        cpd_exclusions: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="sonar.cpd.exclusions duplication-scope patterns"),
        ] = ()
        api_url: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^https://[^/]+$",
                description="SonarCloud web API origin the settings sync writes to",
            ),
        ]
        api_timeout_seconds: Annotated[
            t.PositiveInt,
            m.Field(description="Per-request SonarCloud web API timeout"),
        ]
        issue_exclusions: Annotated[
            t.VariadicTuple[
                FlextInfraModelsConfigSonarcloud.SonarcloudIssueExclusionSpec
            ],
            m.Field(
                description=(
                    "Server-side issue exclusions applied through SonarCloud "
                    "project settings; never written as file properties"
                ),
            ),
        ] = ()


__all__: list[str] = ["FlextInfraModelsConfigRender"]
