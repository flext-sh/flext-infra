"""Project-level integration tests for class nesting file execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
from flext_infra.refactor.service import FlextInfraRefactorService
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


def _project(tmp_path: Path, module: str, body: str) -> Path:
    """Materialize a real project carrying one private module."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    package_dir = tmp_path / "src" / "app" / "_dispatcher"
    package_dir.mkdir(parents=True)
    (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    target_file = package_dir / module
    target_file.write_text(body, encoding="utf-8")
    return target_file


def _refactor(target_file: Path) -> m.Infra.Result:
    """Refactor one file through the public composition root."""
    service = FlextInfraRefactorService()
    tm.ok(service.load_rules())
    return service.orchestrator.refactor_file(target_file, dry_run=True)


class TestsFlextInfraIntegrationRefactorNestingProject:
    """Class nesting across a project tree."""

    def test_project_processes_without_errors(self, tmp_path: Path) -> None:
        """Every loose class in a module is nested under one discovered namespace."""
        target_file = _project(
            tmp_path,
            "dispatcher.py",
            "class TimeoutEnforcer:\n    pass\n\n\nclass RateLimiter:\n    pass\n",
        )
        discovered = tm.ok(
            FlextInfraRefactorLooseClassScanner().derive_class_nesting_mappings(tmp_path)
        )
        namespaces = {entry.target_namespace for entry in discovered}

        result = _refactor(target_file)

        tm.that(result.success, eq=True)
        tm.that(result.modified, eq=True)
        tm.that(len(namespaces), eq=1)
        tm.that(result.refactored_code, has=f"class {namespaces.pop()}:")

    def test_no_type_errors_introduced(self, tmp_path: Path) -> None:
        """Annotations survive the transform untouched."""
        target_file = _project(
            tmp_path,
            "helper.py",
            "class Helper:\n"
            "    def process(self, value: int | None = None) -> int:\n"
            "        return value or 0\n",
        )

        result = _refactor(target_file)

        tm.that(result.success, eq=True)
        tm.that(result.refactored_code, has="value: int | None = None")
