from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraUtilitiesDependencyPathSync
from tests import c, p, t


def _rewrite_dep_paths(
    pyproject_path: Path,
    *,
    mode: c.Infra.PathSyncMode,
    internal_names: set[str],
    workspace_members: t.StrSequence = (),
    is_root: bool = False,
    dry_run: bool = False,
) -> p.Result[t.StrSequence]:
    return FlextInfraUtilitiesDependencyPathSync().rewrite_dep_paths(
        pyproject_path,
        mode=mode,
        internal_names=internal_names,
        workspace_members=workspace_members,
        is_root=is_root,
        dry_run=dry_run,
    )


class TestsFlextInfraDepsPathSyncInit:
    """Behavior contract for FlextInfraUtilitiesDependencyPathSync init/detect/rewrite."""

    def test_path_sync_initialization(self) -> None:
        path_sync = FlextInfraUtilitiesDependencyPathSync()
        tm.that(type(path_sync).__name__, eq="FlextInfraUtilitiesDependencyPathSync")

    def test_detect_mode_workspace(self, tmp_path: Path) -> None:
        (tmp_path / ".gitmodules").touch()
        tm.that(
            FlextInfraUtilitiesDependencyPathSync.detect_mode(tmp_path),
            eq=c.Infra.PathSyncMode.WORKSPACE,
        )

    def test_detect_mode_workspace_parent(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".gitmodules").touch()
        project = workspace / "project"
        project.mkdir()
        tm.that(
            FlextInfraUtilitiesDependencyPathSync.detect_mode(project),
            eq=c.Infra.PathSyncMode.WORKSPACE,
        )

    def test_detect_mode_standalone(self, tmp_path: Path) -> None:
        tm.that(
            FlextInfraUtilitiesDependencyPathSync.detect_mode(tmp_path),
            eq=c.Infra.PathSyncMode.STANDALONE,
        )

    def test_detect_mode_with_nonexistent_path(self, tmp_path: Path) -> None:
        tm.that(
            {c.Infra.PathSyncMode.WORKSPACE, c.Infra.PathSyncMode.STANDALONE},
            has=FlextInfraUtilitiesDependencyPathSync.detect_mode(tmp_path),
        )

    def test_detect_mode_with_path_object(self) -> None:
        tm.that(
            {c.Infra.PathSyncMode.WORKSPACE, c.Infra.PathSyncMode.STANDALONE},
            has=FlextInfraUtilitiesDependencyPathSync.detect_mode(Path("/tmp")),
        )

    def test_dep_name_normalizes_path_inputs(self) -> None:
        tm.that(
            FlextInfraUtilitiesDependencyPathSync.dep_name("../flext-core"),
            eq="flext-core",
        )

    def test_rewrite_dep_paths_with_no_deps(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry.dependencies]\npython = "^3.13"')
        tm.ok(
            _rewrite_dep_paths(
                pyproject,
                mode=c.Infra.PathSyncMode.STANDALONE,
                internal_names=set(),
                dry_run=True,
            ),
        )
