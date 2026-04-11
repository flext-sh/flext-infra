"""Public sync service tests for workspace synchronization."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_core import r
from flext_infra import FlextInfraBaseMkGenerator, FlextInfraSyncService
from tests import m, t, u


def _stub_gen(content: str, *, fail: bool = False) -> FlextInfraBaseMkGenerator:
    class _Gen(FlextInfraBaseMkGenerator):
        @override
        def generate_basemk(
            self,
            settings: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
        ) -> r[str]:
            _ = self
            _ = settings
            return r[str].fail(content) if fail else r[str].ok(content)

    return _Gen()


def _write_project(project_root: Path, name: str) -> None:
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            f'name = "{name}"\n'
            'version = "0.1.0"\n'
            'description = "Demo project"\n'
            'requires-python = ">=3.13"\n'
        ),
        encoding="utf-8",
    )


def _write_workspace(workspace_root: Path) -> tuple[Path, Path]:
    demo_a = workspace_root / "demo-a"
    demo_b = workspace_root / "demo-b"
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "workspace-root"\n'
            'version = "0.1.0"\n'
            "\n"
            "[tool.flext.workspace]\n"
            'members = ["demo-a", "demo-b"]\n'
        ),
        encoding="utf-8",
    )
    _write_project(demo_a, "demo-a")
    _write_project(demo_b, "demo-b")
    return demo_a, demo_b


def _error_text[ValueT](result: r[ValueT]) -> str:
    return result.error or ""


def test_sync_generates_basemk_gitignore_and_makefile(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")

    result = FlextInfraSyncService(
        canonical_root=project_root.parent,
        workspace=project_root,
    ).execute()

    assert result.success, _error_text(result)
    assert result.value.files_changed >= 1
    assert (project_root / "base.mk").exists()
    assert (project_root / ".gitignore").exists()
    assert (project_root / "Makefile").exists()


def test_sync_is_idempotent_on_second_run(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")
    service = FlextInfraSyncService(
        canonical_root=project_root.parent,
        workspace=project_root,
    )

    first_result = service.execute()
    assert first_result.success, _error_text(first_result)
    second_result = service.execute()

    assert second_result.success, _error_text(second_result)
    assert second_result.value.files_changed == 0


def test_sync_fails_when_workspace_root_is_missing() -> None:
    missing_root = Path("/nonexistent/path")

    result = FlextInfraSyncService(workspace=missing_root).execute()

    assert result.failure
    assert "does not exist" in _error_text(result)


def test_sync_fails_when_generator_fails(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")

    result = FlextInfraSyncService(
        canonical_root=project_root.parent,
        generator=_stub_gen("Generation failed", fail=True),
        workspace=project_root,
    ).execute()

    assert result.failure
    assert "Generation failed" in _error_text(result)


def test_sync_fails_when_gitignore_path_is_directory(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")
    (project_root / ".gitignore").mkdir()

    result = FlextInfraSyncService(
        canonical_root=project_root.parent,
        workspace=project_root,
    ).execute()

    assert result.failure
    assert ".gitignore update failed" in _error_text(result)


def test_sync_workspace_root_also_syncs_child_projects(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    demo_a, demo_b = _write_workspace(workspace_root)

    result = FlextInfraSyncService(
        canonical_root=workspace_root,
        workspace=workspace_root,
    ).execute()

    assert result.success, _error_text(result)
    assert (workspace_root / "base.mk").exists()
    assert (workspace_root / "Makefile").exists()
    for project_root in (demo_a, demo_b):
        assert (project_root / "base.mk").exists()
        assert (project_root / "Makefile").exists()


def test_sync_regenerates_project_makefile_without_legacy_passthrough(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    _write_project(project_root, "demo-project")
    (project_root / "Makefile").write_text(
        "# legacy custom target\ncustom-target:\n\t@echo legacy\n",
        encoding="utf-8",
    )

    result = FlextInfraSyncService(
        canonical_root=project_root.parent,
        workspace=project_root,
    ).execute()

    assert result.success, _error_text(result)
    makefile_text = (project_root / "Makefile").read_text(encoding="utf-8")
    assert "custom-target" not in makefile_text
    assert "-include custom.mk" in makefile_text
    assert not (project_root / "custom.mk").exists()


def test_atomic_write_ok(tmp_path: Path) -> None:
    target = tmp_path / "test.txt"

    result = u.Cli.atomic_write_text_file(target, "test content")

    assert result.success, _error_text(result)
    assert result.value is True
    assert target.read_text(encoding="utf-8") == "test content"


def test_atomic_write_fails_when_parent_is_a_file(tmp_path: Path) -> None:
    blocked_parent = tmp_path / "occupied"
    blocked_parent.write_text("occupied", encoding="utf-8")

    result = u.Cli.atomic_write_text_file(blocked_parent / "test.txt", "content")

    assert result.failure
    assert "ensure_dir" in _error_text(result)
