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
        "from flext_core import FlextLogger, FlextVersion, u\n"
        "from flext_core import is_success_result\n\n"
        "class Demo:\n"
        "    def get_value(self) -> str:\n"
        "        return self.value\n\n"
        "    def is_ready(self) -> bool:\n"
        "        return True\n\n"
        "def run(result: object) -> object:\n"
        "    logger = FlextLogger.get_logger('demo')\n"
        "    configured = u.is_structlog_configured()\n"
        "    level = u.get_log_level_from_config()\n"
        "    version = FlextVersion.get_version_string()\n"
        "    info = FlextVersion.get_version_info()\n"
        "    package = FlextVersion.get_package_info()\n"
        "    ready = FlextVersion.is_version_at_least('1.0.0')\n"
        "    if result.is_success:\n"
        "        return (\n"
        "            logger, configured, level, version, info, package, ready,\n"
        "            is_success_result(result),\n"
        "        )\n"
        "    return result\n",
        encoding="utf-8",
    )
    return workspace, source_file


def _build_workspace_many(tmp_path: Path, count: int) -> tuple[Path, tuple[Path, ...]]:
    workspace = tmp_path / "workspace-many"
    project = workspace / "sample-project"
    package_dir = project / "src" / "sample_pkg"
    package_dir.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        "[project]\nname='sample'\ndependencies=['flext-core']\n",
        encoding="utf-8",
    )
    files: list[Path] = []
    for index in range(count):
        source_file = package_dir / f"service_{index}.py"
        source_file.write_text(
            "from __future__ import annotations\n"
            "from flext_core import is_success_result\n\n"
            "def run(result: object) -> object:\n"
            "    if result.is_success:\n"
            "        return is_success_result(result)\n"
            "    return result\n",
            encoding="utf-8",
        )
        files.append(source_file)
    return workspace, tuple(files)


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
            "pyrefly": (),
        },
        {
            "ruff": (),
            "pyrefly": ("pyrefly-after",),
        },
    )


def _snapshot_lints(
    _cls: type[FlextInfraUtilitiesProtectedEdit],
    py_file: Path,
    workspace: Path,
    *,
    gates: list[str] | None = None,
) -> dict[str, tuple[str, ...]]:
    _ = (py_file, workspace, gates)
    return {
        "ruff": (),
        "pyrefly": (),
    }


def _protected_write(
    _cls: type[FlextInfraUtilitiesProtectedEdit],
    py_file: Path,
    *,
    workspace: Path,
    updated_source: str,
    keep_backup: bool = False,
    gates: list[str] | None = None,
) -> tuple[bool, list[str]]:
    _ = (workspace, keep_backup, gates)
    py_file.write_text(updated_source, encoding="utf-8")
    return (True, [])


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
        workspace=workspace,
        dry_run=True,
        projects=["sample-project"],
        preview_limit=5,
    ).execute()

    tm.ok(result)
    report = result.value
    tm.that(report.files_scanned, eq=1)
    tm.that(report.files_with_changes, eq=1)
    tm.that(report.automated_change_count >= 9, eq=True)
    tm.that(report.warning_count >= 2, eq=True)
    tm.that(report.files[0].diff, has="successful_result")
    tm.that(report.files[0].diff, has=".success")
    tm.that(report.files[0].diff, has="fetch_logger")
    tm.that(report.files[0].diff, has="structlog_configured")
    tm.that(report.files[0].diff, has="resolve_log_level_from_config")
    tm.that(report.files[0].diff, has="resolve_version_string")
    tm.that(report.files[0].diff, has="version_at_least")
    tm.that(report.files[0].lint_tools, eq=("ruff", "pyright", "mypy", "pyrefly"))
    tm.that(report.files[0].lint_after["pyrefly"], eq=("pyrefly-after",))
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
        result = infra_main([
            "refactor",
            "accessor-migrate",
            f"--workspace={workspace!s}",
            "--dry-run",
        ])

    tm.that(result, eq=0)
    tm.that(buffer.getvalue(), has="Accessor Migration")


def test_accessor_migration_dry_run_lints_only_previewed_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _files = _build_workspace_many(tmp_path, count=2)
    linted: list[str] = []

    def _counting_preview(
        _cls: type[FlextInfraUtilitiesProtectedEdit],
        py_file: Path,
        workspace: Path,
        *,
        updated_source: str,
        gates: list[str] | None = None,
    ) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
        _ = (workspace, updated_source, gates)
        linted.append(py_file.name)
        return ({}, {})

    monkeypatch.setattr(
        FlextInfraUtilitiesProtectedEdit,
        "preview_source_lint",
        classmethod(_counting_preview),
    )

    result = FlextInfraAccessorMigrationOrchestrator(
        workspace=workspace,
        dry_run=True,
        projects=["sample-project"],
        preview_limit=1,
    ).execute()

    tm.ok(result)
    tm.that(result.value.files_scanned, eq=2)
    tm.that(result.value.files_with_changes, eq=2)
    tm.that(len(result.value.files), eq=1)
    tm.that(linted, eq=[result.value.files[0].file.rsplit("/", maxsplit=1)[-1]])


def test_accessor_migration_apply_writes_updated_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, source_file = _build_workspace(tmp_path)
    monkeypatch.setattr(
        FlextInfraUtilitiesProtectedEdit,
        "lint_snapshot",
        classmethod(_snapshot_lints),
    )
    monkeypatch.setattr(
        FlextInfraUtilitiesProtectedEdit,
        "protected_source_write",
        classmethod(_protected_write),
    )

    result = FlextInfraAccessorMigrationOrchestrator(
        workspace=workspace,
        apply=True,
        dry_run=False,
        projects=["sample-project"],
        preview_limit=5,
    ).execute()

    tm.ok(result)
    updated_source = source_file.read_text(encoding="utf-8")
    tm.that(updated_source, has="successful_result")
    tm.that(updated_source, has="result.success")
    tm.that(updated_source, has="FlextLogger.fetch_logger")
    tm.that(updated_source, has="u.structlog_configured")
    tm.that(updated_source, has="u.resolve_log_level_from_config")
    tm.that(updated_source, has="FlextVersion.resolve_version_string")
    tm.that(updated_source, has="FlextVersion.resolve_version_info")
    tm.that(updated_source, has="FlextVersion.resolve_package_info")
    tm.that(updated_source, has="FlextVersion.version_at_least")
