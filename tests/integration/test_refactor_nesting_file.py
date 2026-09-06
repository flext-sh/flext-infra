"""Integration test for single-file class-nesting execution flow."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
from flext_infra.refactor.service import FlextInfraRefactorService
from flext_tests import tm

if TYPE_CHECKING:
    from tests import m

pytestmark = [pytest.mark.integration]


def _project_with_loose_class(tmp_path: Path) -> tuple[Path, Path]:
    """Materialize a real project whose private module holds a loose class."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    package_dir = tmp_path / "src" / "app" / "_helpers"
    package_dir.mkdir(parents=True)
    (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    target_file = package_dir / "result.py"
    target_file.write_text(
        "class ResultHelpers:\n"
        "    pass\n\n\n"
        "def build(value: ResultHelpers) -> ResultHelpers:\n"
        "    if isinstance(value, ResultHelpers):\n"
        "        return ResultHelpers()\n"
        "    return value\n",
        encoding="utf-8",
    )
    return tmp_path, target_file


class TestsFlextInfraIntegrationRefactorNestingFile:
    """Behavior contract for single-file class nesting."""

    def test_class_nesting_nests_the_loose_class_under_the_discovered_namespace(
        self, tmp_path: Path
    ) -> None:
        """The namespace comes from live discovery, never from a stored mapping."""
        repository_root, target_file = _project_with_loose_class(tmp_path)
        discovered = tm.ok(
            FlextInfraRefactorLooseClassScanner().derive_class_nesting_mappings(
                repository_root
            )
        )
        mapping = next(
            entry for entry in discovered if entry.loose_name == "ResultHelpers"
        )

        service = FlextInfraRefactorService()
        tm.ok(service.load_rules())
        result: m.Infra.Result = service.orchestrator.refactor_file(
            target_file, dry_run=False
        )

        tm.that(result.success, eq=True)
        tm.that(result.modified, eq=True)
        tm.that(result.refactored_code, none=False)
        tm.that(result.refactored_code, has=f"class {mapping.target_namespace}:")
        tm.that(result.refactored_code, has="class ResultHelpers:")
