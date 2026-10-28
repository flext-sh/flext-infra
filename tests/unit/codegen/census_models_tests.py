"""Tests for census models and violation pattern.

Validates CensusViolation/CensusReport models and the compiled violation
regex pattern. Projects without pyproject.toml are filtered at the discovery
boundary, not via a hand-curated list.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import c, m, tm


class TestsFlextInfraModelsCodegenCensus:
    """Violation pattern and census report model contracts."""

    @staticmethod
    def test_named_groups_present() -> None:
        """Test named groups present."""
        match = c.Infra.VIOLATION_PATTERN.match(
            "[ban-cyclic-import] src/file.py:10 — msg",
        )
        tm.ok(match is not None)
        if match is not None:
            tm.that(set(match.groupdict()), eq={"rule", "module", "line", "message"})

    @staticmethod
    def test_model_fields() -> None:
        """Test model fields."""
        v = m.Infra.CensusViolation(
            module="src/file.py",
            rule="NS-001",
            line=10,
            message="Test message",
            fixable=True,
        )
        tm.that(v.module, eq="src/file.py")
        tm.that(v.rule, eq="NS-001")
        tm.that(v.line, eq=10)
        tm.that(v.message, eq="Test message")
        tm.ok(v.fixable)

    @staticmethod
    def test_empty_report() -> None:
        """Test empty report."""
        report = m.Infra.CensusReport(
            project="test-project",
            violations=[],
            total=0,
            fixable=0,
        )
        tm.that(report.project, eq="test-project")
        tm.that(report.total, eq=0)
        tm.that(report.fixable, eq=0)
        tm.that(report.violations, empty=True)

    @staticmethod
    def test_report_with_mixed_violations() -> None:
        """Test report with mixed violations."""
        violations = [
            m.Infra.CensusViolation(
                module="src/a.py",
                rule="NS-000",
                line=1,
                message="m1",
                fixable=False,
            ),
            m.Infra.CensusViolation(
                module="src/b.py",
                rule="NS-001",
                line=2,
                message="m2",
                fixable=True,
            ),
            m.Infra.CensusViolation(
                module="src/c.py",
                rule="NS-002",
                line=3,
                message="m3",
                fixable=True,
            ),
        ]
        report = m.Infra.CensusReport(
            project="test-project",
            violations=violations,
            total=len(violations),
            fixable=sum(1 for v in violations if v.fixable),
        )
        tm.that(report.total, eq=3)
        tm.that(report.fixable, eq=2)

    @staticmethod
    def test_fix_context_factories_keep_accumulation_instance_local() -> None:
        """Fresh factory defaults isolate both violation lists and path sets."""
        first = m.Infra.FixContext()
        second = m.Infra.FixContext()

        first.fix(module="src/first.py", rule="example", line=1, message="fixed")
        first.skip(module="src/second.py", rule="example", line=2, message="skipped")
        first.files_modified.add("src/first.py")

        tm.ok(first.has_changes)
        tm.that(len(first.violations_fixed), eq=1)
        tm.that(len(first.violations_skipped), eq=1)
        tm.fail(second.has_changes)
        tm.that(second.violations_fixed, empty=True)
        tm.that(second.violations_skipped, empty=True)
        tm.that(second.files_modified, empty=True)
