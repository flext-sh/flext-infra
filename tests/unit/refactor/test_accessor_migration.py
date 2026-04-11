from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import main as infra_main
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from flext_infra.refactor.accessor_migration import (
    FlextInfraAccessorMigrationOrchestrator,
)


def _build_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    project = workspace / "sample-project"
    package_dir = project / "src" / "sample_pkg"
    package_dir.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        "[project]\nname='sample'\ndependencies=['flext-core']\n",
        encoding="utf-8",
    )
    source_file = package_dir / "service.py"
    source_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core import is_success_result\n\n"
        "class Demo:\n"
        "    def get_value(self) -> str:\n"
        "        return self.value\n\n"
        "    def is_ready(self) -> bool:\n"
        "        return True\n\n"
        "def run(result: object) -> object:\n"
        "    if result.is_success:\n"
        "        return is_success_result(result)\n"
        "    return result\n",
        encoding="utf-8",
    )
    return workspace, source_file


def _preview_lints(
    _cls: type[FlextInfraUtilitiesProtectedEdit],
    py_file: Path,
    workspace: Path,
    *,
    updated_source: str,
    gates: list[str] | None = None,
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    _ = (py_file, workspace, updated_source, gates)
    return (
        {
            "ruff": ("ruff-before",),
            "mypy": tuple(),
            "pyright": tuple(),
            "pyrefly": tuple(),
        },
        {
            "ruff": tuple(),
            "mypy": ("mypy-after",),
            "pyright": tuple(),
            "pyrefly": tuple(),
        },
    )


def test_accessor_migration_service_reports_preview_and_keeps_file_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, source_file = _build_workspace(tmp_path)
    monkeypatch.setattr(
        FlextInfraUtilitiesProtectedEdit,
        "preview_source_lint",
        classmethod(_preview_lints),
    )
    original_source = source_file.read_text(encoding="utf-8")

    result = FlextInfraAccessorMigrationOrchestrator(
        workspace_root=workspace,
        dry_run=True,
        projects=["sample-project"],
        preview_limit=5,
    ).execute()

    tm.ok(result)
    report = result.value
    tm.that(report.files_scanned, eq=1)
    tm.that(report.files_with_changes, eq=1)
    tm.that(report.automated_change_count >= 2, eq=True)
    tm.that(report.warning_count >= 2, eq=True)
    tm.that(report.files[0].diff, has="successful_result")
    tm.that(report.files[0].diff, has=".success")
    tm.that(report.files[0].lint_after["mypy"], eq=("mypy-after",))
    tm.that(source_file.read_text(encoding="utf-8"), eq=original_source)


def test_accessor_migration_cli_registers_and_runs_dry_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _source_file = _build_workspace(tmp_path)
    monkeypatch.setattr(
        FlextInfraUtilitiesProtectedEdit,
        "preview_source_lint",
        classmethod(_preview_lints),
    )
    buffer = StringIO()

    with redirect_stdout(buffer):
        result = infra_main(
            [
                "refactor",
                "accessor-migrate",
                f"--workspace={workspace!s}",
                "--dry-run",
            ]
        )

    tm.that(result, eq=0)
    tm.that(buffer.getvalue(), has="Accessor Migration")
