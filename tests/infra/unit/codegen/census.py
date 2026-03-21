"""Tests for FlextInfraCodegenCensus service.

Validates violation parsing, fixability classification, and project exclusion
logic without hitting the real workspace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import u

from flext_infra.codegen.census import FlextInfraCodegenCensus
from flext_infra.models import FlextInfraModels


@pytest.fixture
def census(tmp_path: Path) -> FlextInfraCodegenCensus:
    return FlextInfraCodegenCensus(workspace_root=tmp_path)


class TestParseViolationValid:
    @pytest.mark.parametrize(
        (
            "violation_str",
            "expected_rule",
            "expected_module",
            "expected_line",
            "expected_msg",
        ),
        [
            (
                "[NS-000-001] src/file.py:42 — Multiple outer classes found (expected 1, got 2)",
                "NS-000",
                "src/file.py",
                42,
                "Multiple outer classes found (expected 1, got 2)",
            ),
            (
                "[NS-001-001] src/file.py:10 — Loose Final constant 'X' belongs in constants.py",
                "NS-001",
                "src/file.py",
                10,
                "Loose Final constant 'X' belongs in constants.py",
            ),
            (
                "[NS-002-001] src/file.py:5 — TypeVar 'T' belongs in typings.py",
                "NS-002",
                "src/file.py",
                5,
                "TypeVar 'T' belongs in typings.py",
            ),
            (
                "[NS-001-099] src/deep/nested/module.py:999 — Some long message with special chars: !@#",
                "NS-001",
                "src/deep/nested/module.py",
                999,
                "Some long message with special chars: !@#",
            ),
        ],
        ids=["ns000", "ns001", "ns002", "deep-path"],
    )
    def test_parses_fields(
        self,
        violation_str: str,
        expected_rule: str,
        expected_module: str,
        expected_line: int,
        expected_msg: str,
    ) -> None:
        result = FlextInfraCodegenCensus._parse_violation(violation_str)
        u.Tests.Matchers.that(result is not None, eq=True)
        u.Tests.Matchers.that(
            isinstance(result, FlextInfraModels.Infra.CensusViolation),
            eq=True,
        )
        assert result is not None
        u.Tests.Matchers.that(result.rule, eq=expected_rule)
        u.Tests.Matchers.that(result.module, eq=expected_module)
        u.Tests.Matchers.that(result.line, eq=expected_line)
        u.Tests.Matchers.that(result.message, eq=expected_msg)


class TestParseViolationInvalid:
    @pytest.mark.parametrize(
        "violation_str",
        [
            "",
            "random text without brackets",
            "[WRONG-FORMAT] missing fields",
            "[NS-001] src/file.py:10 - wrong dash instead of em-dash",
            "src/file.py:10 — Missing rule prefix",
            "[NS-001-001] no-colon-line — message",
            "[NS-001-001] src/file.py:notanumber — message",
        ],
        ids=[
            "empty",
            "no-brackets",
            "wrong-format",
            "wrong-dash",
            "missing-rule",
            "no-line-number",
            "non-numeric-line",
        ],
    )
    def test_returns_none(self, violation_str: str) -> None:
        u.Tests.Matchers.that(
            FlextInfraCodegenCensus._parse_violation(violation_str) is None,
            eq=True,
        )


class TestFixabilityClassification:
    def test_ns000_not_fixable(self) -> None:
        result = FlextInfraCodegenCensus._parse_violation(
            "[NS-000-001] src/file.py:1 — Structure violation",
        )
        u.Tests.Matchers.that(result is not None, eq=True)
        assert result is not None
        u.Tests.Matchers.that(result.fixable, eq=False)

    def test_ns001_fixable(self) -> None:
        result = FlextInfraCodegenCensus._parse_violation(
            "[NS-001-001] src/file.py:1 — Constant violation",
        )
        u.Tests.Matchers.that(result is not None, eq=True)
        assert result is not None
        u.Tests.Matchers.that(result.fixable, eq=True)

    def test_ns002_fixable(self) -> None:
        result = FlextInfraCodegenCensus._parse_violation(
            "[NS-002-001] src/file.py:1 — TypeVar violation",
        )
        u.Tests.Matchers.that(result is not None, eq=True)
        assert result is not None
        u.Tests.Matchers.that(result.fixable, eq=True)

    def test_ns000_multiple_sub_rules_not_fixable(self) -> None:
        for sub in ("001", "002", "099"):
            result = FlextInfraCodegenCensus._parse_violation(
                f"[NS-000-{sub}] src/x.py:1 — msg",
            )
            u.Tests.Matchers.that(result is not None, eq=True)
            assert result is not None
            u.Tests.Matchers.that(result.fixable, eq=False)


__all__: list[str] = []
