from __future__ import annotations

from collections.abc import (
    Callable,
    Sequence,
)
from pathlib import Path
from typing import override

import pytest
from flext_tests import tm

from flext_infra import FlextInfraInternalDependencySyncService
from tests import p, r, t


def _set_toml_stub(
    service: FlextInfraInternalDependencySyncService,
    values: Sequence[p.Result[t.Infra.ContainerDict]],
) -> None:
    state = {"index": 0}

    def _read(_path: Path) -> p.Result[t.Infra.ContainerDict]:
        item = values[state["index"]]
        state["index"] += 1
        return item

    class _TomlReaderStub:
        def __init__(
            self, fn: Callable[[Path], p.Result[t.Infra.ContainerDict]]
        ) -> None:
            self._fn = fn

        def read_plain(self, path: Path) -> p.Result[t.Infra.ContainerDict]:
            return self._fn(path)

    service.toml = _TomlReaderStub(_read)


class TestSyncMethodEdgeCases:
    def test_sync_with_parsed_repo_map_failure(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.poetry.dependencies]\nflext-core = { path = "../flext-core" }\n',
        )
        (tmp_path / "flext-repo-map.toml").write_text("invalid toml {")
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {"flext-core": {"path": "../flext-core"}},
                        },
                    },
                    "project": {},
                }),
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {"flext-core": {"path": "../flext-core"}},
                        },
                    },
                    "project": {},
                }),
            ],
        )
        tm.fail(service.sync(tmp_path))

    def test_sync_with_workspace_mode_and_gitmodules(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".gitmodules").write_text(
            '[submodule "flext-core"]\n\turl = git@github.com:flext-sh/flext-core.git\n',
        )
        project = workspace / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            '[tool.poetry.dependencies]\nflext-core = { path = "../flext-core" }\n',
        )

        class _TestService(FlextInfraInternalDependencySyncService):
            @override
            def ensure_checkout(
                self,
                dep_path: Path,
                repo_url: str,
                ref_name: str,
            ) -> p.Result[bool]:
                _ = (dep_path, repo_url, ref_name)
                return r[bool].ok(True)

        service = _TestService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {"flext-core": {"path": "../flext-core"}},
                        },
                    },
                    "project": {},
                }),
            ],
        )
        monkeypatch.setenv("FLEXT_WORKSPACE_ROOT", str(workspace))
        tm.that(service.sync(project).success, eq=True)

    def test_sync_with_synthesized_repo_map(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[tool.poetry.dependencies]\nflext-core = { path = "../flext-core" }\n',
        )

        class _TestService(FlextInfraInternalDependencySyncService):
            @override
            def infer_owner_from_origin(self, project_root: Path) -> str | None:
                _ = project_root
                return "flext-sh"

            @override
            def ensure_checkout(
                self,
                dep_path: Path,
                repo_url: str,
                ref_name: str,
            ) -> p.Result[bool]:
                _ = (dep_path, repo_url, ref_name)
                return r[bool].ok(True)

        service = _TestService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {"flext-core": {"path": "../flext-core"}},
                        },
                    },
                    "project": {},
                }),
            ],
        )
        tm.that(service.sync(tmp_path).success, eq=True)

    def test_sync_missing_repo_mapping(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[tool.poetry.dependencies]\nflext-core = { path = "../flext-core" }\n',
        )
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {"flext-core": {"path": "../flext-core"}},
                        },
                    },
                    "project": {},
                }),
            ],
        )

        tm.fail(service.sync(tmp_path))

    def test_sync_symlink_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".gitmodules").write_text(
            '[submodule "flext-core"]\n\turl = git@github.com:flext-sh/flext-core.git\n',
        )
        (workspace / "flext-core").mkdir()
        project = workspace / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            '[tool.poetry.dependencies]\nflext-core = { path = "../flext-core" }\n',
        )

        class _TestService(FlextInfraInternalDependencySyncService):
            @override
            def ensure_symlink(self, dep_path: Path, sibling: Path) -> p.Result[bool]:
                _ = (dep_path, sibling)
                return r[bool].fail("symlink failed")

        service = _TestService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {"flext-core": {"path": "../flext-core"}},
                        },
                    },
                    "project": {},
                }),
            ],
        )
        monkeypatch.setenv("FLEXT_WORKSPACE_ROOT", str(workspace))
        tm.fail(service.sync(project))
