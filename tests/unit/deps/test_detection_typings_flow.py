from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import (
    FlextInfraDependencyDetectionService,
    FlextInfraUtilitiesSubprocess,
    FlextInfraUtilitiesTomlParse,
)
from tests import m, t


class _StubReadPlain:
    """Stub for read_plain returning predefined values in sequence."""

    def __init__(self, values: Sequence[r[Mapping[str, t.Infra.InfraValue]]]) -> None:
        self._values = values
        self._idx = 0

    def __call__(self, path: Path) -> r[Mapping[str, t.Infra.InfraValue]]:
        _ = path
        value = self._values[self._idx]
        if self._idx < len(self._values) - 1:
            self._idx += 1
        return value


class _StubRunRaw:
    """Stub for run_raw returning a predefined result."""

    def __init__(self, result: r[m.Infra.CommandOutput]) -> None:
        self._result = result

    def __call__(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[m.Infra.CommandOutput]:
        _ = cmd, cwd, timeout, env
        return self._result


class TestModuleAndTypingsFlow:
    def test_module_to_types_package(self) -> None:
        service = FlextInfraDependencyDetectionService()
        tm.that(service.module_to_types_package("yaml", {}), eq="types-pyyaml")
        tm.that(service.module_to_types_package("flext_core", {}), eq=None)
        module_to_package: Mapping[str, t.Infra.InfraValue] = {
            "yaml": "custom-types-yaml",
        }
        typing_libraries: Mapping[str, t.Infra.InfraValue] = {
            "module_to_package": module_to_package,
        }
        limits: Mapping[str, t.Infra.InfraValue] = {
            "typing_libraries": typing_libraries,
        }
        tm.that(service.module_to_types_package("yaml", limits), eq="custom-types-yaml")
        tm.that(service.module_to_types_package("unknown_module", {}), eq=None)
        tm.that(service.module_to_types_package("yaml.parser", {}), eq="types-pyyaml")

    def test_get_current_typings_from_pyproject(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        payload: Mapping[str, t.Infra.InfraValue] = {
            "tool": {
                "poetry": {
                    "group": {
                        "typings": {
                            "dependencies": {
                                "types-pyyaml": "^6.0",
                                "types-requests": "^2.28",
                            },
                        },
                    },
                },
            },
        }
        monkeypatch.setattr(
            FlextInfraUtilitiesTomlParse,
            "read_plain",
            _StubReadPlain([r[Mapping[str, t.Infra.InfraValue]].ok(payload)]),
        )
        got = service.get_current_typings_from_pyproject(Path("/dummy"))
        tm.that(got, eq=[])

    def test_get_current_typings_from_pyproject_variants(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        monkeypatch.setattr(
            FlextInfraUtilitiesTomlParse,
            "read_plain",
            _StubReadPlain([
                r[Mapping[str, t.Infra.InfraValue]].ok({
                    "project": {
                        "optional-dependencies": {
                            "typings": [
                                "types-pyyaml>=6.0",
                                "types-requests[extra]==2.28",
                            ],
                        },
                    },
                }),
                r[Mapping[str, t.Infra.InfraValue]].ok({
                    "project": {
                        "optional-dependencies": {
                            "typings": {"types-pyyaml": ">=6.0"},
                        },
                    },
                }),
                r[Mapping[str, t.Infra.InfraValue]].fail("not found"),
                r[Mapping[str, t.Infra.InfraValue]].ok({}),
            ]),
        )
        path = Path("/dummy")
        tm.that(service.get_current_typings_from_pyproject(path), eq=[])
        tm.that(service.get_current_typings_from_pyproject(path), eq=[])
        tm.that(service.get_current_typings_from_pyproject(path), eq=[])
        tm.that(service.get_current_typings_from_pyproject(path), eq=[])

    def test_get_required_typings_paths(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "mypy").write_text("")
        out = m.Infra.CommandOutput(exit_code=0, stdout="", stderr="")
        service = FlextInfraDependencyDetectionService()
        monkeypatch.setattr(
            FlextInfraUtilitiesSubprocess,
            "run_raw",
            _StubRunRaw(r[m.Infra.CommandOutput].ok(out)),
        )
        monkeypatch.setattr(
            FlextInfraUtilitiesTomlParse,
            "read_plain",
            _StubReadPlain([
                r[Mapping[str, t.Infra.InfraValue]].ok({}),
                r[Mapping[str, t.Infra.InfraValue]].ok({
                    "project": {"optional-dependencies": {"typings": []}},
                }),
            ]),
        )
        tm.ok(service.get_required_typings(tmp_path, venv_bin))
        monkeypatch.setattr(
            FlextInfraUtilitiesTomlParse,
            "read_plain",
            _StubReadPlain([
                r[Mapping[str, t.Infra.InfraValue]].ok({}),
                r[Mapping[str, t.Infra.InfraValue]].ok({}),
            ]),
        )
        tm.ok(service.get_required_typings(tmp_path, venv_bin, include_mypy=False))
        monkeypatch.setattr(
            FlextInfraUtilitiesSubprocess,
            "run_raw",
            _StubRunRaw(r[m.Infra.CommandOutput].fail("mypy crash")),
        )
        monkeypatch.setattr(
            FlextInfraUtilitiesTomlParse,
            "read_plain",
            _StubReadPlain([r[Mapping[str, t.Infra.InfraValue]].ok({})]),
        )
        tm.fail(service.get_required_typings(tmp_path, venv_bin))
