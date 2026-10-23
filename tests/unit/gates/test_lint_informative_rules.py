"""Every reported native finding blocks without an advisory-rule catalog.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, u
from tests import c, tm


class TestsFlextInfraLintFindings:
    """Even a warning supplied by a native owner remains blocking."""

    @staticmethod
    def test_warning_findings_block_the_verdict() -> None:
        """Severity cannot waive a real diagnostic."""
        warning = m.Infra.Issue(
            file="src/sample.py",
            line=1,
            column=1,
            code="native-warning",
            message="native diagnostic",
            severity=c.Infra.GateSeverity.WARNING.value,
        )
        tm.that(u.Infra.blocking_gate_findings((warning,)), eq=(warning,))
