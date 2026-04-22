"""Scenario dataclasses for parametrized testing of infrastructure services.

Provides scenario definitions using flext_tests base classes (m, t).
Eliminates duplication and serves as single source of truth for infra test cases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from tests import m, t


class TestsFlextInfraSubprocessScenario(m.Value):
    """Single scenario for subprocess operation testing using m.Value."""

    __test__ = False

    name: Annotated[t.NonEmptyStr, m.Field(description="Scenario name")]
    cmd: Annotated[t.StrSequence, m.Field(description="Command tokens to execute")]
    expected_output: Annotated[
        str,
        m.Field(default="", description="Expected standard output"),
    ]
    should_succeed: Annotated[
        bool,
        m.Field(default=True, description="Whether the command should succeed"),
    ]
    description: Annotated[
        str | None,
        m.Field(default=None, description="Optional scenario description"),
    ]


class TestsFlextInfraGitScenario(m.Value):
    """Single scenario for git operation testing using m.Value."""
