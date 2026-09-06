"""Integration test for single-file class-nesting execution flow."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c
from flext_infra.refactor.file_executor import FlextInfraRefactorFileExecutor
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from tests import m, t

pytestmark = [pytest.mark.integration]


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


class TestsFlextInfraIntegrationRefactorNestingFile:
    """Behavior contract for test_refactor_nesting_file."""

    def test_class_nesting_refactor_single_file_end_to_end(
        self, tmp_path: Path
    ) -> None:
        """Verify a loose class is nested under its module facade and repointed."""
        module_file = _write_project(
            tmp_path,
            package="pkg",
            module="single_file_refactor_target.py",
            source=(
                '"""Fixture module exercising class-nesting derivation."""\n\n'
                "from __future__ import annotations\n\n"
                '__all__ = ["FlextUtilities"]\n\n\n'
                "class FlextUtilities:\n"
                '    """Module facade nesting target."""\n\n\n'
                "class ResultHelpers:\n"
                '    """Loose class expected to nest under the facade."""\n\n\n'
                "def build(value: ResultHelpers) -> ResultHelpers:\n"
                "    if isinstance(value, ResultHelpers):\n"
                "        return ResultHelpers()\n"
                "    return value\n"
            ),
        )
        result = _apply_rule(tmp_path, module_file, dry_run=False)
        # The module declares its own facade (FlextUtilities) via __all__, so the
        # loose ResultHelpers class derives that facade as its nesting target and
        # every reference to ResultHelpers is repointed to the nested location.
        tm.that(result.success, eq=True)
        tm.that(result.modified, eq=True)
        tm.that(result.refactored_code, none=False)
        tm.that(result.refactored_code, has="class FlextUtilities:")
        tm.that(result.refactored_code, has="class ResultHelpers:")
        tm.that(result.refactored_code, has="FlextUtilities.ResultHelpers")

    def test_class_nesting_refactor_without_facade_reports_no_target_namespace(
        self, tmp_path: Path
    ) -> None:
        """Verify a module with no derivable facade family fails the precheck."""
        module_file = _write_project(
            tmp_path,
            package="pkg",
            module="orphan.py",
            source=(
                '"""Fixture module with no declared facade family."""\n\n'
                "from __future__ import annotations\n\n\n"
                "class Orphan:\n"
                '    """Loose class with nowhere to nest."""\n'
            ),
        )
        result = _apply_rule(tmp_path, module_file, dry_run=False)
        tm.that(result.success, eq=False)
        tm.that(result.modified, eq=False)
        tm.that("|".join(result.changes), has="no_target_namespace")
