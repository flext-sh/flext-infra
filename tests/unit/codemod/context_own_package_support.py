"""Shared codemod rule fixtures for own-package context contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m


class TestsFlextInfraContextOwnPackageSupport:
    """Rule fixtures shared by the own-package context contract modules."""

    @staticmethod
    def private_import_rule() -> m.Infra.CodemodRule:
        """Return the own-package private-import probe rule.

        Returns:
            The resulting ``m.Infra.CodemodRule``.

        """
        """Return the own-package private-import probe rule.

        Returns:
            The resulting ``m.Infra.CodemodRule``.

        """
        return m.Infra.CodemodRule(
            id="private-import-probe",
            digest="probe",
            provider="probe",
            resource=Path("probe.yml"),
            fixable=False,
            context=(
                m.Infra.CodemodContextCondition(
                    variable="MOD",
                    predicate=c.Infra.CodemodContextPredicate.OWN_PACKAGE,
                    holds=False,
                ),
            ),
        )
