"""Idempotency tests for class nesting file execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner
from flext_infra.refactor.service import FlextInfraRefactorService
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


def _project_with_loose_class(tmp_path: Path) -> Path:
    """Materialize a real project whose private module holds a loose class."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    package_dir = tmp_path / "src" / "app" / "_dispatcher"
    package_dir.mkdir(parents=True)
    (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    target_file = package_dir / "timeout.py"
    target_file.write_text("class TimeoutEnforcer:\n    pass\n", encoding="utf-8")
    return target_file


def _refactor(target_file: Path, *, dry_run: bool) -> m.Infra.Result:
    """Refactor one file through the public composition root."""
    service = FlextInfraRefactorService()
    tm.ok(service.load_rules())
    return service.orchestrator.refactor_file(target_file, dry_run=dry_run)


class TestsFlextInfraIntegrationRefactorNestingIdempotency:
    """Running the nesting refactor repeatedly converges after the first run."""

    def test_first_run_produces_changes(self, tmp_path: Path) -> None:
        """First run nests the loose class under the discovered namespace."""
        target_file = _project_with_loose_class(tmp_path)
        discovered = tm.ok(
            FlextInfraRefactorLooseClassScanner().derive_class_nesting_mappings(tmp_path)
        )
        mapping = next(
            entry for entry in discovered if entry.loose_name == "TimeoutEnforcer"
        )

        result = _refactor(target_file, dry_run=False)

        tm.that(result.modified, eq=True)
        tm.that(result.refactored_code, none=False)
        tm.that(result.refactored_code, has=f"class {mapping.target_namespace}:")

    def test_second_run_produces_no_changes(self, tmp_path: Path) -> None:
        """A file already nested is left untouched by the next run."""
        target_file = _project_with_loose_class(tmp_path)
        first = _refactor(target_file, dry_run=False)
        target_file.write_text(tm.not_none(first.refactored_code), encoding="utf-8")

        second = _refactor(target_file, dry_run=True)

        tm.that(second.success, eq=True)
        tm.that(second.modified, eq=False)

    def test_third_run_produces_no_changes(self, tmp_path: Path) -> None:
        """Convergence holds across repeated applications."""
        target_file = _project_with_loose_class(tmp_path)
        for _ in range(3):
            result = _refactor(target_file, dry_run=False)
            if result.modified and result.refactored_code is not None:
                target_file.write_text(result.refactored_code, encoding="utf-8")

        final_result = _refactor(target_file, dry_run=True)

        tm.that(final_result.success, eq=True)
        tm.that(final_result.modified, eq=False)
