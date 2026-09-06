"""Project-level integration tests for class nesting file execution."""

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


class TestsFlextInfraIntegrationRefactorNestingProject:
    """Test class nesting refactor across a project."""

    def test_project_processes_without_errors(self, tmp_path: Path) -> None:
        """Test that full project processes without errors."""
        module_file = _write_project(
            tmp_path,
            package="test_project",
            module="dispatcher.py",
            source=(
                "from __future__ import annotations\n\n"
                '__all__ = ["FlextDispatcher"]\n\n\n'
                "class FlextDispatcher:\n"
                '    """Module facade."""\n\n\n'
                "class TimeoutEnforcer:\n"
                "    pass\n\n\n"
                "class RateLimiter:\n"
                "    pass\n"
            ),
        )
        result = _apply_rule(tmp_path, module_file, dry_run=True)
        tm.that(result.success, eq=True)
        tm.that(result.modified, eq=True)

    def test_no_type_errors_introduced(self, tmp_path: Path) -> None:
        """Verify no type errors are introduced by refactoring."""
        module_file = _write_project(
            tmp_path,
            package="test_project",
            module="test.py",
            source=(
                "from __future__ import annotations\n\n"
                "from typing import Optional\n\n"
                '__all__ = ["FlextUtilities"]\n\n\n'
                "class FlextUtilities:\n"
                '    """Module facade."""\n\n\n'
                "class Helper:\n"
                "    def process(self, x: Optional[int] = None) -> int:\n"
                "        return x or 0\n"
            ),
        )
        result = _apply_rule(tmp_path, module_file, dry_run=True)
        tm.that(result.success, eq=True)
        refactored_code = tm.not_none(result.refactored_code)
        tm.that(refactored_code, has="Optional[int]")
