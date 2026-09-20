"""Common assertion helpers for namespace validator tests.

Provides reusable assertion patterns to eliminate duplication
in test verification code across rule-specific test files.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u


class TestsFlextInfraValidateAssertions:
    """Common assertion patterns for namespace validation tests."""

    def __init__(self) -> None:
        self._validator = FlextInfraNamespaceValidator()

    @property
    def validator(self) -> FlextInfraNamespaceValidator:
        return self._validator

    def assert_project_passes(
        self, tmp_path: Path, *, module_source: str, module_name: str
    ) -> None:
        """Assert that a project with the given module passes validation."""
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name=module_name
        )
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=True, msg=str(result.value.violations))
        tm.that(result.value.violations, empty=True)

    def assert_project_fails(
        self,
        tmp_path: Path,
        *,
        module_source: str,
        module_name: str,
        expected_violation_substr: str,
    ) -> None:
        """Assert that a project with the given module fails with expected violation."""
        root = u.Tests.namespace_project(
            tmp_path, module_source=module_source, module_name=module_name
        )
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=False, msg=str(result.value.violations))
        tm.that(
            any(expected_violation_substr in v for v in result.value.violations),
            eq=True,
            msg=f"Expected violation containing '{expected_violation_substr}' not found in: {result.value.violations}",
        )

    def assert_project_at_path_passes(
        self, tmp_path: Path, *, module_source: str, module_path: str
    ) -> None:
        """Assert that a project at specific path passes validation."""
        root, _ = u.Tests.namespace_project_path(
            tmp_path, module_source=module_source, module_path=module_path
        )
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=True, msg=str(result.value.violations))
        tm.that(result.value.violations, empty=True)

    def assert_valid_module(self, root: Path, *, expected_violations: int = 0) -> None:
        """Assert that an already-created project root passes validation."""
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=True, msg=str(result.value.violations))
        tm.that(len(result.value.violations), eq=expected_violations)

    def assert_invalid_module(
        self,
        root: Path,
        *,
        expected_violation_substr: str,
        expected_violation_count: int | None = None,
    ) -> None:
        """Assert that an already-created project root fails validation."""
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(result.value.passed, eq=False, msg=str(result.value.violations))
        tm.that(
            any(expected_violation_substr in v for v in result.value.violations),
            eq=True,
            msg=f"Expected violation containing '{expected_violation_substr}' not found in: {result.value.violations}",
        )
        if expected_violation_count is not None:
            tm.that(len(result.value.violations), eq=expected_violation_count)

    def assert_no_violation_contains(self, root: Path, substring: str) -> None:
        """Assert that no violation contains the given substring."""
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(
            any(substring in v for v in result.value.violations),
            eq=False,
            msg=f"Unexpected violation containing '{substring}' found in: {result.value.violations}",
        )

    def assert_violation_code_prefix(self, root: Path, prefix: str) -> None:
        """Assert that at least one violation has the given code prefix."""
        result = self.validator.validate_project(root)
        tm.ok(result)
        tm.that(
            any(v.startswith(f"[{prefix}") for v in result.value.violations),
            eq=True,
            msg=f"Expected violation with prefix '[{prefix}' not found in: {result.value.violations}",
        )


__all__: list[str] = ["TestsFlextInfraValidateAssertions"]
