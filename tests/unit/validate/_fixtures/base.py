"""Base test class for namespace validator tests.

Provides common setup, validator instantiation, and shared test infrastructure
to eliminate duplication across rule-specific test files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import m, u

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraValidateNamespaceBase:
    """Base test class for namespace validator rule tests.

    Each rule-specific test class should inherit from this base to share
    common validator setup and project creation patterns.
    """

    @property
    def validator(self) -> FlextInfraNamespaceValidator:
        """Fresh validator instance per test for isolation."""
        return FlextInfraNamespaceValidator()

    def _create_namespace_project(
        self, tmp_path: Path, *, module_source: str, module_name: str
    ) -> Path:
        """Create a namespace test project with the given module source."""
        return u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name=module_name
        )

    def _create_namespace_project_path(
        self, tmp_path: Path, *, module_source: str, module_path: str
    ) -> t.Pair[Path, Path]:
        """Create a namespace test project at a specific module path."""
        return u.Tests.namespace_project_path(
            tmp_path, module_source=module_source, module_path=module_path
        )

    def _validate_project(self, root: Path) -> m.Infra.ValidationReport:
        """Run validator on project and return successful result."""
        result = self.validator.validate_project(root)
        tm.ok(result)
        return result.value

    def _assert_valid(self, root: Path) -> None:
        """Assert that the project passes validation with no violations."""
        report = self._validate_project(root)
        tm.that(report.passed, eq=True, msg=str(report.violations))
        tm.that(report.violations, empty=True)

    def _assert_invalid(
        self,
        root: Path,
        *,
        expected_violation_substr: str | None = None,
        expected_violation_count: int | None = None,
    ) -> None:
        """Assert that the project fails validation with expected violations."""
        report = self._validate_project(root)
        tm.that(report.passed, eq=False, msg=str(report.violations))
        if expected_violation_substr is not None:
            tm.that(
                any(expected_violation_substr in v for v in report.violations),
                eq=True,
                msg=f"Expected violation containing '{expected_violation_substr}' not found in: {report.violations}",
            )
        if expected_violation_count is not None:
            tm.that(len(report.violations), eq=expected_violation_count)

    def _assert_violation_contains(self, root: Path, substring: str) -> None:
        """Assert that at least one violation contains the given substring."""
        report = self._validate_project(root)
        tm.that(
            any(substring in v for v in report.violations),
            eq=True,
            msg=f"Expected violation containing '{substring}' not found in: {report.violations}",
        )

    def _assert_no_violation_contains(self, root: Path, substring: str) -> None:
        """Assert that no violation contains the given substring."""
        report = self._validate_project(root)
        tm.that(
            any(substring in v for v in report.violations),
            eq=False,
            msg=f"Unexpected violation containing '{substring}' found in: {report.violations}",
        )

    def _assert_file_in_inventory(self, root: Path, target: Path) -> None:
        """Assert that a target file is in the source inventory."""
        files = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(root,))
        )
        tm.ok(files)
        tm.that(
            target in files.value,
            eq=True,
            msg=f"namespace fixture omitted from source inventory: {target}; {files.value}",
        )


__all__: list[str] = ["TestsFlextInfraValidateNamespaceBase"]
