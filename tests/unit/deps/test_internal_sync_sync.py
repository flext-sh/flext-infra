from __future__ import annotations

import os
from collections.abc import (
    Callable,
    Generator,
    Sequence,
)
from contextlib import contextmanager
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraInternalDependencySyncService, r
from tests.protocols import p
from tests.typings import t


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


@contextmanager
def _temporary_env(overrides: dict[str, str]) -> Generator[None]:
    original = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[key] = value
        yield
    finally:
        for key, previous in original.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


class TestsFlextInfraDepsInternalSyncSync:
    def test_sync_no_deps(self, tmp_path: Path) -> None:
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(
            service,
            [r[t.Infra.ContainerDict].ok({"tool": {}, "project": {}})],
        )
        (tmp_path / "pyproject.toml").write_text("")
        tm.ok(service.sync(tmp_path), eq=0)

    def test_sync_collect_failure(self, tmp_path: Path) -> None:
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(service, [r[t.Infra.ContainerDict].fail("read error")])
        (tmp_path / "pyproject.toml").write_text("")
        tm.fail(service.sync(tmp_path))

    def test_sync_workspace_mode_symlink(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / ".gitmodules").write_text(
            '[submodule "flext-api"]\n\tpath = flext-api\n\turl = git@github.com:flext-sh/flext-api.git\n',
        )
        (workspace / "flext-api").mkdir()
        project = workspace / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("")
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {
                                "flext-api": {"path": ".flext-deps/flext-api"},
                            },
                        },
                    },
                    "project": {},
                }),
            ],
        )
        with _temporary_env({"FLEXT_STANDALONE": "", "FLEXT_WORKSPACE_ROOT": ""}):
            tm.ok(service.sync(project))

    def test_sync_missing_repo_mapping(
        self,
        tmp_path: Path,
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("")
        (project / "flext-repo-map.toml").write_text("")
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(
            service,
            [
                r[t.Infra.ContainerDict].ok({
                    "tool": {
                        "poetry": {
                            "dependencies": {
                                "flext-api": {"path": ".flext-deps/flext-api"},
                            },
                        },
                    },
                    "project": {},
                }),
                r[t.Infra.ContainerDict].ok({"repo": {}}),
            ],
        )
        with _temporary_env({"FLEXT_STANDALONE": "", "FLEXT_WORKSPACE_ROOT": ""}):
            error = tm.fail(service.sync(project))
        tm.that(error, contains="missing repo mapping")
