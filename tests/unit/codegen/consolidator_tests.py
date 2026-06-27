"""Tests for the public constants consolidator command service."""

from __future__ import annotations

import json
from pathlib import Path

from flext_tests import tm

from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
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


def _build_consolidator_workspace(tmp_path: Path) -> Path:
    """Create a workspace with one project whose constants define a demo value."""
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
    (package_dir / "__init__.py").write_text(
        "from flext_demo.constants import c\n",
        encoding="utf-8",
    )
    (package_dir / "constants.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from types import SimpleNamespace\n"
        "from typing import Final\n"
        "\n"
        'DEMO_VALUE: Final[str] = "demo"\n'
        "c = SimpleNamespace(DEMO_VALUE=DEMO_VALUE)\n",
        encoding="utf-8",
    )
    (package_dir / "consumer.py").write_text(
        'from __future__ import annotations\n\nVALUE = "demo"\n',
        encoding="utf-8",
    )
    return workspace_root


def test_execute_apply_mode_replaces_literal_with_canonical_reference(
    tmp_path: Path,
) -> None:
    workspace_root = _build_consolidator_workspace(tmp_path)
    consumer_path = workspace_root / "flext-demo" / "src" / "flext_demo" / "consumer.py"

    result = u.Tests.consolidate_codegen(
        workspace_root=workspace_root,
        dry_run=False,
    )

    tm.ok(result)
    tm.that(result.value, has="Applied 1 replacements")
    updated_source = consumer_path.read_text(encoding="utf-8")
    tm.that(updated_source, has="VALUE = c.DEMO_VALUE")
    tm.that(updated_source, has="from flext_demo import c")


def test_execute_apply_mode_json_output(tmp_path: Path) -> None:
    workspace_root = _build_consolidator_workspace(tmp_path)
    service = FlextInfraCodegenConsolidator(
        workspace=workspace_root,
        dry_run=False,
        output_format="json",
    )

    result = service.execute()

    tm.ok(result)
    payload = json.loads(result.value)
    assert payload["total_found"] == 1
    assert payload["total_applied"] == 1
    assert payload["total_failed"] == 0
    assert len(payload["files"]) == 1
    assert payload["files"][0]["status"] == "applied"


def test_execute_dry_run_json_output(tmp_path: Path) -> None:
    workspace_root = _build_consolidator_workspace(tmp_path)
    service = FlextInfraCodegenConsolidator(
        workspace=workspace_root,
        dry_run=True,
        output_format="json",
    )

    result = service.execute()

    tm.ok(result)
    payload = json.loads(result.value)
    assert payload["total_found"] == 1
    assert payload["total_applied"] == 0
    assert payload["total_failed"] == 0
    assert payload["files"] == []


__all__: t.StrSequence = []
