"""Tests for real workspace rewrites after MRO migration."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraRefactorMROImportRewriter
from tests import m


def _build_workspace(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace_root = tmp_path
    project_root = workspace_root / "flext-demo"
    package_root = project_root / "src" / "demo_pkg"
    package_root.mkdir(parents=True)
    (project_root / ".git").mkdir()
    (project_root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        "[project]\nname = 'flext-demo'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    constants_path = package_root / "constants.py"
    constants_path.write_text(
        "from __future__ import annotations\n\n"
        'FOO = "value"\n\n'
        "class FlextDemoConstants:\n"
        "    pass\n\n"
        "c = FlextDemoConstants\n",
        encoding="utf-8",
    )
    consumer_path = package_root / "consumer.py"
    consumer_path.write_text(
        "from __future__ import annotations\n\n"
        "from demo_pkg.constants import FOO\n\n"
        "value = FOO\n",
        encoding="utf-8",
    )
    return (workspace_root, constants_path, consumer_path)


def _scan_report(constants_path: Path) -> m.Infra.MROScanReport:
    return m.Infra.MROScanReport(
        file=str(constants_path),
        module="demo_pkg.constants",
        constants_class="FlextDemoConstants",
        facade_alias="c",
        candidates=(
            m.Infra.MROSymbolCandidate(
                symbol="FOO",
                line=3,
                kind="constant",
                class_name="",
                facade_name="c",
            ),
        ),
    )


def test_migrate_workspace_applies_consumer_rewrites(tmp_path: Path) -> None:
    workspace_root, constants_path, consumer_path = _build_workspace(tmp_path)

    migrations, rewrites, errors = (
        FlextInfraRefactorMROImportRewriter.migrate_workspace(
            workspace_root=workspace_root,
            scan_results=[_scan_report(constants_path)],
            apply=True,
        )
    )

    assert errors == ()
    assert len(migrations) == 1
    assert migrations[0].moved_symbols == ("FOO",)
    assert any(item.file.endswith("consumer.py") for item in rewrites)

    constants_text = constants_path.read_text(encoding="utf-8")
    consumer_text = consumer_path.read_text(encoding="utf-8")

    assert 'class FlextDemoConstants:\n    FOO = "value"' in constants_text
    assert "from demo_pkg.constants import FOO" not in consumer_text
    assert "from demo_pkg.constants import c" in consumer_text
    assert "value = c.FOO" in consumer_text


def test_migrate_workspace_dry_run_preserves_files(tmp_path: Path) -> None:
    workspace_root, constants_path, consumer_path = _build_workspace(tmp_path)
    original_constants = constants_path.read_text(encoding="utf-8")
    original_consumer = consumer_path.read_text(encoding="utf-8")

    migrations, rewrites, errors = (
        FlextInfraRefactorMROImportRewriter.migrate_workspace(
            workspace_root=workspace_root,
            scan_results=[_scan_report(constants_path)],
            apply=False,
        )
    )

    assert errors == ()
    assert len(migrations) == 1
    assert any(item.file.endswith("consumer.py") for item in rewrites)
    assert constants_path.read_text(encoding="utf-8") == original_constants
    assert consumer_path.read_text(encoding="utf-8") == original_consumer
