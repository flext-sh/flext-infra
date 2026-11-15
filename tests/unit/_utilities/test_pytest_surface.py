"""``u.Infra.Pytest`` publishes pytest's own functions with their own contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import tm, u


class TestsFlextInfraUtilitiesPytestSurface:
    """Both pytest fixture call forms keep pytest's runtime and static contract."""

    @u.Tests.fixture
    @staticmethod
    def bare_form_value() -> int:
        """Provide a value through the bare decorator form.

        Returns:
            The resulting ``int``.

        """
        return 1

    @u.Tests.fixture(scope="class", name="factory_form_value")
    @staticmethod
    def factory_form() -> int:
        """Provide a renamed class-scoped value through the factory form.

        Returns:
            The resulting ``int``.

        """
        return 2

    @staticmethod
    def test_both_call_forms_register_pytest_fixtures(
        bare_form_value: int,
        factory_form_value: int,
    ) -> None:
        """Pytest resolves the bare and the renamed factory-form fixtures."""
        tm.that((bare_form_value, factory_form_value), eq=(1, 2))
