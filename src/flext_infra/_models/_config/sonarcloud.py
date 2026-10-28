"""Foundational declarations for SonarCloud configuration policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import Annotated

from flext_cli import m, t

from flext_infra._models._config.contract import FlextInfraModelsConfigContract


class FlextInfraModelsConfigSonarcloud:
    """SonarCloud policy records resolved before aggregate configuration."""

    class SonarcloudIssueExclusionSpec(FlextInfraModelsConfigContract.ConfigContract):
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


__all__: list[str] = ["FlextInfraModelsConfigSonarcloud"]
