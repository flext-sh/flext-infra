"""Idempotency tests for class nesting file execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.refactor.file_executor import FlextInfraRefactorFileExecutor
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m, t


class _FileRuleHarness(FlextInfraRefactorFileExecutor):
    def __init__(self) -> None:
        self._class_nesting_policy_by_family = None
        self._class_nesting_gate = None

    def apply_rule(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool,
    ) -> m.Infra.Result:
        """Expose class nesting through the integration harness contract."""
        return self._apply_file_rule_selection(
            c.Infra.RefactorFileRuleKind.CLASS_NESTING,
            {},
            rope_project,
            resource,
            dry_run=dry_run,
        )


def _write_project(tmp_path: Path, *, package: str, module: str, source: str) -> Path:
    """Materialize a minimal project (pyproject.toml + src/<package>/<module>)."""
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "{package}"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    package_dir = tmp_path / "src" / package
    package_dir.mkdir(parents=True, exist_ok=True)
    module_file = package_dir / module
    module_file.write_text(source, encoding="utf-8")
    return module_file


def _apply_rule(
    repository_root: Path, file_path: Path, *, dry_run: bool
) -> m.Infra.Result:
    rule = _FileRuleHarness()
    rope_project = u.Infra.init_rope_project(repository_root)
    try:
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            raise FileNotFoundError(file_path)
        return rule.apply_rule(rope_project, resource, dry_run=dry_run)
    finally:
        rope_project.close()


_FACADE_MODULE_SOURCE = (
    "from __future__ import annotations\n\n"
    '__all__ = ["FlextDispatcher"]\n\n\n'
    "class FlextDispatcher:\n"
    '    """Module facade."""\n\n\n'
    "class TimeoutEnforcer:\n"
    "    pass\n"
)


class TestsFlextInfraIntegrationRefactorNestingIdempotency:
    """Test that running refactor multiple times is idempotent."""

    def test_first_run_produces_changes(self, tmp_path: Path) -> None:
        """First run should produce changes."""
        module_file = _write_project(
            tmp_path, package="pkg", module="test.py", source=_FACADE_MODULE_SOURCE
        )
        result = _apply_rule(tmp_path, module_file, dry_run=False)
        tm.that(result.modified, eq=True)
        tm.that(result.refactored_code, none=False)
        tm.that(result.refactored_code, has="class FlextDispatcher:")
        tm.that(result.refactored_code, has="class TimeoutEnforcer:")

    def test_second_run_produces_no_changes(self, tmp_path: Path) -> None:
        """Second run on already-refactored code should produce no changes."""
        module_file = _write_project(
            tmp_path, package="pkg", module="test.py", source=_FACADE_MODULE_SOURCE
        )
        result1 = _apply_rule(tmp_path, module_file, dry_run=False)
        refactored_code = tm.not_none(result1.refactored_code)
        module_file.write_text(refactored_code, encoding="utf-8")
        result2 = _apply_rule(tmp_path, module_file, dry_run=True)
        tm.that(result2.success, eq=True)
        tm.that(result2.modified, eq=False)

    def test_third_run_produces_no_changes(self, tmp_path: Path) -> None:
        """Third run should also produce no changes."""
        module_file = _write_project(
            tmp_path, package="pkg", module="test.py", source=_FACADE_MODULE_SOURCE
        )
        for _ in range(3):
            result = _apply_rule(tmp_path, module_file, dry_run=False)
            if result.modified and result.refactored_code is not None:
                module_file.write_text(result.refactored_code, encoding="utf-8")
        final_result = _apply_rule(tmp_path, module_file, dry_run=True)
        tm.that(final_result.success, eq=True)
        tm.that(final_result.modified, eq=False)
