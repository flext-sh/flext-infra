"""Declarative SonarCloud policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m, t

from flext_infra._models._config.contract import FlextInfraConfigModelsContract


class FlextInfraConfigModelsRender:
    """Policy declarations consumed by the configuration contract."""

    class SonarcloudIssueExclusionSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One SonarCloud issue exclusion applied as a server-side project setting.

        SonarCloud automatic analysis ignores ``sonar.issue.ignore.*`` in
        ``.sonarcloud.properties``; the exclusion lives in each project's
        SonarCloud settings. This record is its single fleet owner, rendered
        into the generated file only as documentation.
        """

        rule_key: Annotated[
            t.NonEmptyStr,
            m.Field(description="Sonar rule key, e.g. 'text:S8565'"),
        ]
        resource_key: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project-relative resource pattern"),
        ]
        reason: Annotated[
            t.NonEmptyStr,
            m.Field(description="Operator justification and bead"),
        ]

    class SonarcloudSpec(FlextInfraConfigModelsContract.ConfigContract):
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
            t.VariadicTuple[FlextInfraConfigModelsRender.SonarcloudIssueExclusionSpec],
            m.Field(
                description=(
                    "Server-side issue exclusions applied through SonarCloud "
                    "project settings; never written as file properties"
                ),
            ),
        ] = ()
