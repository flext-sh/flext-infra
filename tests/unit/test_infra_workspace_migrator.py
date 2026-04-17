from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraProjectMigrator
from tests import u


def test_migrator_dry_run_reports_changes_without_writes(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    u.Infra.Tests.write_migrator_project(project_root)
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "NEW_BASE\n",
        workspace_root=tmp_path,
        dry_run=True,
    )
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(any(c.startswith("[DRY-RUN]") for c in migrations[0].changes), eq=True)
    tm.that((project_root / "base.mk").read_text(encoding="utf-8"), eq="OLD_BASE\n")


def test_migrator_apply_updates_project_files(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    u.Infra.Tests.write_migrator_project(project_root)
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "NEW_BASE\n",
        workspace_root=tmp_path,
        dry_run=False,
    )
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(migrations[0].errors, eq=[])
    tm.that((project_root / "base.mk").exists(), eq=True)
    tm.that((project_root / "base.mk").read_text(encoding="utf-8"), eq="NEW_BASE\n")
    makefile_text = (project_root / "Makefile").read_text(encoding="utf-8")
    tm.that("scripts/check/workspace_check.py" not in makefile_text, eq=True)
    tm.that(makefile_text, has="python -m flext_infra check run")


def test_migrator_handles_missing_pyproject_gracefully(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir(parents=True, exist_ok=True)
    (project_root / "base.mk").write_text("OLD_BASE\n", encoding="utf-8")
    (project_root / "Makefile").write_text("", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "NEW_BASE\n",
        workspace_root=tmp_path,
        dry_run=False,
    )
    result = migrator.execute()
    tm.ok(result)
    tm.that((project_root / "base.mk").read_text(encoding="utf-8"), eq="NEW_BASE\n")


def test_migrator_preserves_custom_makefile_content(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    u.Infra.Tests.write_migrator_project(project_root)
    custom = "# Custom rule\ncustom-target:\n\t@echo 'custom'\n"
    (project_root / "Makefile").write_text(custom, encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "NEW_BASE\n",
        workspace_root=tmp_path,
        dry_run=False,
    )
    result = migrator.execute()
    tm.ok(result)
    text = (project_root / "Makefile").read_text(encoding="utf-8")
    tm.that(text, has="custom-target")
    tm.that(text, has="@echo 'custom'")


def test_migrator_workspace_root_not_exists(tmp_path: Path) -> None:
    migrator = FlextInfraProjectMigrator(
        workspace=tmp_path / "nonexistent", dry_run=False, apply_changes=True
    )
    result = migrator.execute()
    tm.fail(result, has="does not exist")


def test_migrator_discovery_failure(tmp_path: Path) -> None:
    migrator = FlextInfraProjectMigrator(
        workspace=tmp_path, dry_run=False, apply_changes=True
    )
    migrator.discovery = u.Infra.Tests.create_migrator_discovery(
        error="Discovery failed"
    )
    result = migrator.execute()
    tm.fail(result, has="Discovery failed")


def test_migrator_execute_returns_failure(tmp_path: Path) -> None:
    migrator = FlextInfraProjectMigrator(
        workspace=tmp_path, dry_run=False, apply_changes=True
    )
    migrator.discovery = u.Infra.Tests.create_migrator_discovery(
        error="Execution failed"
    )
    result = migrator.execute()
    tm.fail(result, has="Execution failed")


def test_migrator_workspace_root_project_detection(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "Makefile").touch()
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()
    migrator = FlextInfraProjectMigrator(
        workspace=tmp_path, dry_run=True, apply_changes=False
    )
    migrator.discovery = u.Infra.Tests.create_migrator_discovery([])
    migrator.generator = u.Infra.Tests.create_migrator_generator("base.mk")
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(len(migrations), gte=1)


def test_migrator_no_changes_needed(tmp_path: Path) -> None:
    project_root = tmp_path / "project-a"
    project_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "Makefile").write_text("migrated", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        '[project]\ndependencies = ["flext-core @ ../flext-core"]\n',
        encoding="utf-8",
    )
    (project_root / ".gitignore").write_text(
        ".reports/\n.venv/\n__pycache__/\nbase.mk\n",
        encoding="utf-8",
    )
    (project_root / "base.mk").write_text("base.mk", encoding="utf-8")
    migrator = u.Infra.Tests.build_project_migrator(
        u.Infra.Tests.create_migrator_project(project_root),
        "base.mk",
        workspace_root=tmp_path,
        dry_run=False,
    )
    result = migrator.execute()
    migrations = tm.ok(result)
    tm.that(migrations[0].changes, has="no changes needed")
