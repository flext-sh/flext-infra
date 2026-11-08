"""``u.Infra.Pytest`` publishes pytest's own functions with their own contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.gates import FlextInfraGatesPyright
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


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

    @staticmethod
    @c.Tests.MARK.slow
    def test_fixture_keeps_every_pytest_overload_for_pyright(
        tmp_path: Path,
    ) -> None:
        """Strict Pyright accepts both forms and reveals pytest's exact overloads."""
        project = u.Tests.mk_project(
            tmp_path,
            "pytest-surface",
            pyproject=(
                '[project]\nname = "pytest-surface"\nversion = "0.1.0"\n'
                '[tool.pyright]\ntypeCheckingMode = "strict"\n'
            ),
            with_src=True,
        )
        (project / "src" / "pytest_surface" / "consumer.py").write_text(
            "import pytest\n"
            "from flext_infra import u\n"
            "\n"
            "\n"
            "def provide() -> int:\n"
            "    return 1\n"
            "\n"
            "\n"
            "@u.Infra.Pytest.fixture\n"
            "def bare() -> int:\n"
            "    return 1\n"
            "\n"
            "\n"
            '@u.Infra.Pytest.fixture(scope="module", autouse=False, name="named")\n'
            "def factory() -> int:\n"
            "    return 1\n"
            "\n"
            "\n"
            "reveal_type(u.Infra.Pytest.fixture)\n"
            "reveal_type(pytest.fixture)\n"
            "reveal_type(u.Infra.Pytest.fixture(provide))\n"
            "reveal_type(pytest.fixture(provide))\n"
            'reveal_type(u.Infra.Pytest.fixture(scope="module", name="named"))\n'
            'reveal_type(pytest.fixture(scope="module", name="named"))\n'
            "reveal_type(u.Infra.Pytest.raises)\n"
            "reveal_type(pytest.raises)\n"
            "reveal_type(u.Infra.Pytest.warns)\n"
            "reveal_type(pytest.warns)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        result = FlextInfraGatesPyright(repository_root=project).check(
            project,
            m.Infra.GateContext.model_validate({
                "repository_root": project,
                "reports_dir": tmp_path / "native",
            }),
        )
        revealed = tuple(
            issue.message.rpartition(" is ")[2]
            for issue in result.issues
            if issue.severity == "information"
        )
        tm.that(
            tuple(issue for issue in result.issues if issue.severity != "information"),
            eq=(),
            msg=result.raw_output,
        )
        tm.that(len(revealed), eq=10, msg=result.raw_output)
        tm.that(revealed[0::2], eq=revealed[1::2], msg=result.raw_output)
