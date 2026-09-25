"""Namespace validation support composed through the public test utilities."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraNamespaceValidator, u
from tests import m, t, u as test_u


class TestsFlextInfraUtilitiesNamespaceMixin:
    """Shared behavior for tests of the public namespace validator."""

    class NamespaceFixture:
        """Build real projects and verify observable namespace diagnostics."""

        @property
        def validator(self) -> FlextInfraNamespaceValidator:
            """Fresh validator instance for each public operation."""
            return FlextInfraNamespaceValidator()

        def _create_namespace_project(
            self, tmp_path: Path, *, module_source: str, module_name: str
        ) -> Path:
            """Create a tracked project through the canonical fixture owner."""
            return test_u.Tests.namespace_project(
                tmp_path, module_source=module_source, module_name=module_name
            )

        def _create_namespace_project_path(
            self, tmp_path: Path, *, module_source: str, module_path: str
        ) -> t.Pair[Path, Path]:
            """Create a tracked project at the requested module path."""
            return test_u.Tests.namespace_project_path(
                tmp_path, module_source=module_source, module_path=module_path
            )

        def _validate_project(self, root: Path) -> m.Infra.ValidationReport:
            """Require the public validation operation to complete."""
            return tm.ok(self.validator.validate_project(root))

        def _assert_valid(self, root: Path) -> None:
            """Require no namespace violations in the real project."""
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
            """Require the requested namespace failure evidence."""
            report = self._validate_project(root)
            tm.that(report.passed, eq=False, msg=str(report.violations))
            if expected_violation_substr is not None:
                tm.that(
                    any(
                        expected_violation_substr in item for item in report.violations
                    ),
                    eq=True,
                    msg=f"Expected violation containing '{expected_violation_substr}' not found in: {report.violations}",
                )
            if expected_violation_count is not None:
                tm.that(len(report.violations), eq=expected_violation_count)

        def _assert_violation_contains(self, root: Path, substring: str) -> None:
            """Require one diagnostic containing the requested evidence."""
            report = self._validate_project(root)
            tm.that(
                any(substring in item for item in report.violations),
                eq=True,
                msg=f"Expected violation containing '{substring}' not found in: {report.violations}",
            )

        def _assert_no_violation_contains(self, root: Path, substring: str) -> None:
            """Require absence of the specified diagnostic."""
            report = self._validate_project(root)
            tm.that(
                any(substring in item for item in report.violations),
                eq=False,
                msg=f"Unexpected violation containing '{substring}' found in: {report.violations}",
            )

        def _assert_file_in_inventory(self, root: Path, target: Path) -> None:
            """Require the validator input to include the tracked source file."""
            files = tm.ok(
                u.Infra.iter_python_files(
                    m.Infra.SourceScanRequest(project_roots=(root,))
                )
            )
            tm.that(
                target in files,
                eq=True,
                msg=f"namespace fixture omitted from source inventory: {target}; {files}",
            )


__all__: list[str] = ["TestsFlextInfraUtilitiesNamespaceMixin"]
