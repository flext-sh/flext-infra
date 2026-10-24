"""Fresh-import completeness: every exported pydantic class builds at import.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.validate import FlextInfraValidateFreshImport
from tests import tm

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class TestsFlextInfraFreshImportCompleteness:
    """The export probe fails on incomplete models and passes complete ones."""

    @staticmethod
    def test_incomplete_family_model_fails(
        fixture_tree: Callable[[str], Path],
        suite_runtime_root: Path,
    ) -> None:
        """A field naming a sibling through its unbound family stays incomplete."""
        scenarios = fixture_tree("pydantic-completeness")
        report = tm.ok(
            FlextInfraValidateFreshImport(
                repository_root=scenarios / "red",
                runtime_root=suite_runtime_root,
            ).build_report(packages=("flext_completeness_fixture",)),
        )
        tm.fail(report.passed)
        tm.that(report.violations[0], has="1 incomplete pydantic class(es)")
        tm.that(report.violations[0], has="FixtureModels.Entry")
        tm.that(report.violations[0], lacks="FixtureModels.Child")

    @staticmethod
    def test_complete_family_model_passes(
        fixture_tree: Callable[[str], Path],
        suite_runtime_root: Path,
    ) -> None:
        """A sibling declared first and named bare completes at import."""
        scenarios = fixture_tree("pydantic-completeness")
        report = tm.ok(
            FlextInfraValidateFreshImport(
                repository_root=scenarios / "green",
                runtime_root=suite_runtime_root,
            ).build_report(packages=("flext_completeness_fixture",)),
        )
        tm.that(report.passed, eq=True, msg=str(report.violations))
