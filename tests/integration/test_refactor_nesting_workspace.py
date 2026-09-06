"""Workspace-level integration tests for class nesting across governed projects."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.refactor.class_nesting_analyzer import (
    FlextInfraRefactorClassNestingAnalyzer,
)
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration]


class TestsFlextInfraIntegrationRefactorNestingWorkspace:
    """Every governed project derives its own nesting target from its facade."""

    @staticmethod
    def _project(root: Path, *, package: str, module: str, source: str) -> Path:
        """Materialize one governed project (PEP 621 identity + src/<package>)."""
        root.mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{package}"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        package_dir = root / "src" / package
        package_dir.mkdir(parents=True)
        module_file = package_dir / module
        module_file.write_text(source, encoding="utf-8")
        return module_file

    def test_each_project_targets_the_facade_its_module_declares(
        self, tmp_path: Path
    ) -> None:
        """Loose classes in different projects nest under different facades."""
        facades = {"project_a": "FlextModels", "project_b": "FlextUtilities"}
        files = [
            self._project(
                tmp_path / package,
                package=package,
                module="core.py",
                source=(
                    f'class Loose{facade}:\n    pass\n\n\n__all__ = ["{facade}"]\n'
                ),
            )
            for package, facade in facades.items()
        ]

        report = FlextInfraRefactorClassNestingAnalyzer.analyze_files(files)

        targets = {
            violation.class_name: violation.target_namespace
            for violation in report.violations
        }
        tm.that(targets, eq={f"Loose{facade}": facade for facade in facades.values()})

    def test_cross_project_consumer_reports_no_violation_of_its_own(
        self, tmp_path: Path
    ) -> None:
        """A module that only imports another project's class declares nothing loose."""
        owner = self._project(
            tmp_path / "project_a",
            package="project_a",
            module="core.py",
            source='class CoreService:\n    pass\n\n\n__all__ = ["FlextModels"]\n',
        )
        consumer = self._project(
            tmp_path / "project_b",
            package="project_b",
            module="consumer.py",
            source=(
                "from project_a.core import CoreService\n\n\n"
                "def use_service(svc: CoreService) -> None:\n    pass\n"
            ),
        )

        report = FlextInfraRefactorClassNestingAnalyzer.analyze_files([owner, consumer])

        tm.that(
            [
                (violation.class_name, violation.target_namespace)
                for violation in report.violations
            ],
            eq=[("CoreService", "FlextModels")],
        )
