"""Tests for the public constants consolidator command service."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_cli import m as cli_m
from flext_infra.codegen.consolidator import FlextInfraCodegenConsolidator
from tests.typings import t
from tests.utilities import u


class _ConsolidatorFilePayload(cli_m.ContractModel):
    """Typed JSON row emitted by the consolidator command."""

    file: str = cli_m.Field(description="Relative file path")
    status: str = cli_m.Field(description="File processing status")
    changes: t.StrSequence = cli_m.Field(description="Changes applied to the file")


class _ConsolidatorJsonPayload(cli_m.ContractModel):
    """Typed JSON payload emitted by the consolidator command."""

    total_found: int = cli_m.Field(description="Total replacements found")
    total_applied: int = cli_m.Field(description="Total replacements applied")
    total_failed: int = cli_m.Field(description="Total files that failed")
    files: t.SequenceOf[_ConsolidatorFilePayload] = cli_m.Field(
        description="Per-file consolidator results",
    )


def _consolidator_payload(value: str) -> _ConsolidatorJsonPayload:
    """Load and validate consolidator JSON output."""
    payload: _ConsolidatorJsonPayload = _ConsolidatorJsonPayload.model_validate_json(
        value
    )
    return payload


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
        "[project]\nname='flext-demo'\nversion='0.1.0'\n"
        "\n"
        "[tool.mypy]\n"
        'mypy_path = ["src"]\n',
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
        "[project]\nname='flext-demo'\nversion='0.1.0'\n"
        "\n"
        "[tool.mypy]\n"
        'mypy_path = ["src"]\n',
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


def _write_wrapper_consumers(workspace_root: Path) -> t.SequenceOf[Path]:
    """Create wrapper-surface consumers for constants consolidation."""
    project_root = workspace_root / "flext-demo"
    consumer_paths = (
        project_root / "examples" / "consumer.py",
        project_root / "scripts" / "consumer.py",
        project_root / "tests" / "test_consumer.py",
    )
    for consumer_path in consumer_paths:
        consumer_path.parent.mkdir(parents=True, exist_ok=True)
        consumer_path.write_text(
            'from __future__ import annotations\n\nVALUE = "demo"\n',
            encoding="utf-8",
        )
    return consumer_paths


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


def test_execute_apply_mode_scans_wrapper_surfaces(tmp_path: Path) -> None:
    workspace_root = _build_consolidator_workspace(tmp_path)
    package_consumer_path = (
        workspace_root / "flext-demo" / "src" / "flext_demo" / "consumer.py"
    )
    wrapper_consumer_paths = _write_wrapper_consumers(workspace_root)
    service = FlextInfraCodegenConsolidator(
        workspace=workspace_root,
        dry_run=False,
        output_format="json",
    )

    result = service.execute()

    tm.ok(result)
    payload = _consolidator_payload(result.value)
    assert payload.total_found == 4
    assert payload.total_applied == 4
    assert payload.total_failed == 0
    assert len(payload.files) == 4
    for consumer_path in (package_consumer_path, *wrapper_consumer_paths):
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
    payload = _consolidator_payload(result.value)
    assert payload.total_found == 1
    assert payload.total_applied == 1
    assert payload.total_failed == 0
    assert len(payload.files) == 1
    assert payload.files[0].status == "applied"


def test_execute_dry_run_json_output(tmp_path: Path) -> None:
    workspace_root = _build_consolidator_workspace(tmp_path)
    service = FlextInfraCodegenConsolidator(
        workspace=workspace_root,
        dry_run=True,
        output_format="json",
    )

    result = service.execute()

    tm.ok(result)
    payload = _consolidator_payload(result.value)
    assert payload.total_found == 1
    assert payload.total_applied == 0
    assert payload.total_failed == 0
    assert payload.files == []


__all__: t.StrSequence = []
