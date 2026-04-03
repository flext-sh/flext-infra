"""Tests for declarative rope hook execution."""

from __future__ import annotations

from pathlib import Path

from tests import m, u


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


def test_run_rope_post_hooks_applies_mro_migration(tmp_path: Path) -> None:
    workspace_root, constants_path, consumer_path = _build_workspace(tmp_path)

    results: list[m.Infra.Result] = list(
        u.run_rope_post_hooks(workspace_root, dry_run=False)
    )

    assert any(
        result.file_path == consumer_path and result.modified for result in results
    )
    assert 'class FlextDemoConstants:\n    FOO = "value"' in constants_path.read_text(
        encoding="utf-8",
    )
    consumer_text = consumer_path.read_text(encoding="utf-8")
    assert "from demo_pkg.constants import c" in consumer_text
    assert "value = c.FOO" in consumer_text


def test_run_rope_post_hooks_dry_run_is_non_mutating(tmp_path: Path) -> None:
    workspace_root, constants_path, consumer_path = _build_workspace(tmp_path)
    original_constants = constants_path.read_text(encoding="utf-8")
    original_consumer = consumer_path.read_text(encoding="utf-8")

    results: list[m.Infra.Result] = list(
        u.run_rope_post_hooks(workspace_root, dry_run=True)
    )

    assert any(result.file_path == consumer_path for result in results)
    assert all(not result.modified for result in results)
    assert constants_path.read_text(encoding="utf-8") == original_constants
    assert consumer_path.read_text(encoding="utf-8") == original_consumer
