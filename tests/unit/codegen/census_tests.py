"""Tests for FlextInfraCodegenCensus service.

Validates violation parsing, fixability classification, and project exclusion
logic without hitting the real workspace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import r
from flext_infra.codegen.census import FlextInfraCodegenCensus
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


def _parse_violation(violation: str) -> r[m.Infra.CensusViolation]:
    parsed = u.Infra.parse_namespace_validation(
        r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(passed=True, violations=[violation])
        )
    )
    if parsed.failure:
        return r[m.Infra.CensusViolation].from_failure(parsed)
    violations = parsed.unwrap()
    if not violations:
        return r[m.Infra.CensusViolation].fail("no violations parsed from report")
    return r[m.Infra.CensusViolation].ok(violations[0])


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
        result = _parse_violation(violation_str)
        violation = tm.ok(result)
        tm.that(violation, is_=m.Infra.CensusViolation)
        tm.that(violation.rule, eq=expected_rule)
        tm.that(violation.module, eq=expected_module)
        tm.that(violation.line, eq=expected_line)
        tm.that(violation.message, eq=expected_msg)


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
        tm.that(_parse_violation(violation_str), ok=False)


class TestFixabilityClassification:
    def test_ns000_not_fixable(self) -> None:
        result = _parse_violation("[NS-000-001] src/file.py:1 — Structure violation")
        violation = tm.ok(result)
        tm.that(not violation.fixable, eq=True)

    def test_ns001_fixable(self) -> None:
        result = _parse_violation("[NS-001-001] src/file.py:1 — Constant violation")
        violation = tm.ok(result)
        tm.that(violation.fixable, eq=True)

    def test_ns002_fixable(self) -> None:
        result = _parse_violation("[NS-002-001] src/file.py:1 — TypeVar violation")
        violation = tm.ok(result)
        tm.that(violation.fixable, eq=True)

    def test_ns000_multiple_sub_rules_not_fixable(self) -> None:
        for sub in ("001", "002", "099"):
            result = _parse_violation(f"[NS-000-{sub}] src/x.py:1 — msg")
            violation = tm.ok(result)
            tm.that(not violation.fixable, eq=True)


class TestCensusExecute:
    def test_execute_fails_when_apply_changes_requested(self, tmp_path: Path) -> None:
        result = FlextInfraCodegenCensus(
            repository_root=tmp_path, apply_changes=True
        ).execute()

        tm.fail(
            result, has="census is read-only; use flext-infra codegen auto-fix --apply"
        )


__all__: t.StrSequence = []
