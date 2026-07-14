from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import r
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from tests import t

from pathlib import Path

from tests import p



class _TomlStub:
    """Typed stub implementing TomlReader protocol for testing."""

    def __init__(self, values: t.SequenceOf[p.Result[t.Infra.ContainerDict]]) -> None:
        self._values = values
        self._index = 0

    def read_plain(self, path: Path) -> p.Result[t.Infra.ContainerDict]:
        """Return next pre-configured result."""
        _ = path
        item = self._values[self._index]
        self._index += 1
        return item


def _set_toml_stub(
    service: FlextInfraInternalDependencySyncService,
    values: t.SequenceOf[p.Result[t.Infra.ContainerDict]],
) -> None:
    service.toml = _TomlStub(values)


class TestsFlextInfraDepsInternalSyncSyncEdgeMore:
    def test_sync_no_dependencies(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        service = FlextInfraInternalDependencySyncService()
        _set_toml_stub(
            service, [r[t.Infra.ContainerDict].ok({"project": {"name": "test"}})]
        )
        tm.ok(service.sync(tmp_path), eq=0)
