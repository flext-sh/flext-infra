"""The complexity rule family reports at warning severity and still blocks.

The declared family keeps its warning label on every report surface, while
the gate verdict retains every finding: no advisory class survives the 0.12
gate baseline (tracker key operator-ruling-2026-10-09-gate-baseline-0122).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c, config, m, u


class TestsFlextInfraLintInformativeRules:
    """The declared family is labeled a warning and blocks like every finding."""

    @staticmethod
    def test_ssot_declares_the_complexity_family() -> None:
        """Test ssot declares the complexity family."""
        declared = config.Infra.tooling.tools.ruff.informative_rules
        assert "too-many-arguments" in declared
        assert "too-many-positional-arguments" in declared
        assert "too-many-locals" in declared
        assert "too-many-return-statements" in declared
        assert "too-many-branches" in declared
        assert "too-many-public-methods" in declared
        assert "too-many-statements" in declared
        assert "complex-structure" in declared

    @staticmethod
    def test_advisory_rules_report_at_warning_severity() -> None:
        """Test advisory rules report at warning severity."""
        advisory = config.Infra.tooling.tools.ruff.informative_rules
        for code in advisory:
            tm.that(
                u.Infra.ruff_finding_severity(code, advisory),
                eq=c.Infra.GateSeverity.WARNING.value,
            )

    @staticmethod
    def test_undeclared_rules_report_at_error_severity() -> None:
        """Test undeclared rules report at error severity."""
        advisory = frozenset(config.Infra.tooling.tools.ruff.informative_rules)
        blocking = next(
            name
            for name in ("undefined-name", "banned-api", "line-too-long")
            if name not in advisory
        )
        tm.that(
            u.Infra.ruff_finding_severity(blocking, advisory),
            eq=c.Infra.GateSeverity.ERROR.value,
        )

    @staticmethod
    def test_warning_findings_block_the_verdict() -> None:
        """A warning-labeled finding blocks exactly like an error finding."""
        advisory = config.Infra.tooling.tools.ruff.informative_rules
        warning = m.Infra.Issue(
            file="src/sample.py",
            line=1,
            column=1,
            code=next(iter(advisory)),
            message="advisory finding",
            severity=c.Infra.GateSeverity.WARNING.value,
        )
        error = m.Infra.Issue(
            file="src/sample.py",
            line=2,
            column=1,
            code="undefined-name",
            message="blocking finding",
            severity=c.Infra.GateSeverity.ERROR.value,
        )
        tm.that(u.Infra.blocking_gate_findings((warning,)), eq=(warning,))
        tm.that(
            u.Infra.blocking_gate_findings((warning, error)),
            eq=(warning, error),
        )
