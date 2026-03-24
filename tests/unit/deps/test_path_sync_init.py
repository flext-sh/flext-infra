from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_tests import tm

from flext_infra import FlextInfraDependencyPathSync, t


def rewrite_dep_paths(
    pyproject_path: Path,
    *,
    mode: str,
    internal_names: set[str],
    is_root: bool = False,
    dry_run: bool = False,
) -> r[t.StrSequence]:
    return FlextInfraDependencyPathSync().rewrite_dep_paths(
        pyproject_path,
        mode=mode,
        internal_names=internal_names,
        is_root=is_root,
        dry_run=dry_run,
    )


class TestFlextInfraDependencyPathSync:
    def test_path_sync_initialization(self) -> None:
        path_sync = FlextInfraDependencyPathSync()
        tm.that(type(path_sync).__name__, eq="FlextInfraDependencyPathSync")


class TestDetectMode:
    def test_detect_mode_workspace(self, tmp_path: Path) -> None:
        (tmp_path / ".gitmodules").touch()
        tm.that(FlextInfraDependencyPathSync.detect_mode(tmp_path), eq="workspace")

    def test_detect_mode_workspace_parent(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".gitmodules").touch()
        project = workspace / "project"
        project.mkdir()
        tm.that(FlextInfraDependencyPathSync.detect_mode(project), eq="workspace")

    def test_detect_mode_standalone(self, tmp_path: Path) -> None:
        tm.that(FlextInfraDependencyPathSync.detect_mode(tmp_path), eq="standalone")


def test_detect_mode_with_nonexistent_path(tmp_path: Path) -> None:
    tm.that(
        {"workspace", "standalone"},
        has=FlextInfraDependencyPathSync.detect_mode(tmp_path),
    )


def test_detect_mode_with_path_object() -> None:
    tm.that(
        {"workspace", "standalone"},
        has=FlextInfraDependencyPathSync.detect_mode(Path("/tmp")),
    )


class TestPathSyncEdgeCases:
    def test_detect_mode_with_nonexistent_path(self, tmp_path: Path) -> None:
        tm.that(
            {"workspace", "standalone"},
            has=FlextInfraDependencyPathSync.detect_mode(tmp_path),
        )

    def test_extract_dep_name_with_empty_string(self) -> None:
        tm.that(FlextInfraDependencyPathSync.extract_dep_name(""), eq="")

    def test_rewrite_dep_paths_with_no_deps(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry.dependencies]\npython = "^3.13"')
        tm.ok(
            rewrite_dep_paths(
                pyproject,
                mode="poetry",
                internal_names=set(),
                dry_run=True,
            ),
        )
