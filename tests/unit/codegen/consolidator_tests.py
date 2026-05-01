"""Tests for the public constants consolidator command service."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import t, u


def test_execute_scans_real_package_layout(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(parents=True)
    (workspace_root / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["flext-demo"]\n',
        encoding="utf-8",
    )
    project_root = workspace_root / "flext-demo"
    package_dir = project_root / "src" / "flext_demo"
    package_dir.mkdir(parents=True)
    (project_root / "pyproject.toml").write_text(
        "[project]\nname='flext-demo'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "constants.py").write_text(
        "class FlextDemoConstants:\n    pass\n\nc = FlextDemoConstants\n",
        encoding="utf-8",
    )
    (package_dir / "module.py").write_text("VALUE = 1\n", encoding="utf-8")

    result = u.Tests.consolidate_codegen(
        workspace_root=workspace_root,
        dry_run=True,
    )

    tm.ok(result)
    tm.that(result.value, has="Found")


__all__: t.StrSequence = []
