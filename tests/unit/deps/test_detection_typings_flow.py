from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService
from tests import m, r, t, u


class _StubTomlReadJson:
    """Stub for u.Cli.toml_read_json returning predefined values in sequence."""

    def __init__(self, values: Sequence[r[t.Cli.JsonMapping]]) -> None:
        self._values = values
        self._idx = 0

    def __call__(self, path: Path) -> r[t.Cli.JsonMapping]:
        _ = path
        value = self._values[self._idx]
        if self._idx < len(self._values) - 1:
            self._idx += 1
        return value


def _json_mapping(value: t.Infra.InfraMapping) -> t.Cli.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


class _StubRunRaw:
    """Stub for run_raw returning a predefined result."""

    def __init__(self, result: r[m.Cli.CommandOutput]) -> None:
        self._result = result

    def __call__(
        self,
        cmd: t.StrSequence,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[m.Cli.CommandOutput]:
        _ = cmd, cwd, timeout, env
        return self._result


class TestModuleAndTypingsFlow:
    def test_module_to_types_package(self) -> None:
        service = FlextInfraDependencyDetectionService()
        tm.that(service.module_to_types_package("yaml", {}), eq="types-pyyaml")
        tm.that(service.module_to_types_package("flext_core", {}), eq=None)
        module_to_package: t.Infra.InfraMapping = {
            "yaml": "custom-types-yaml",
        }
        typing_libraries: t.Infra.InfraMapping = {
            "module_to_package": module_to_package,
        }
        limits: t.Infra.InfraMapping = {
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
        payload: t.Infra.InfraMapping = {
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
            u.Cli,
            "toml_read_json",
            _StubTomlReadJson([r[t.Cli.JsonMapping].ok(_json_mapping(payload))]),
        )
        got = service.get_current_typings_from_pyproject(Path("/dummy"))
        tm.that(got, eq=[])

    def test_get_current_typings_from_pyproject_variants(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        monkeypatch.setattr(
            u.Cli,
            "toml_read_json",
            _StubTomlReadJson([
                r[t.Cli.JsonMapping].ok(
                    _json_mapping({
                        "project": {
                            "optional-dependencies": {
                                "typings": [
                                    "types-pyyaml>=6.0",
                                    "types-requests[extra]==2.28",
                                ],
                            },
                        },
                    })
                ),
                r[t.Cli.JsonMapping].ok(
                    _json_mapping({
                        "project": {
                            "optional-dependencies": {
                                "typings": {"types-pyyaml": ">=6.0"},
                            },
                        },
                    })
                ),
                r[t.Cli.JsonMapping].fail("not found"),
                r[t.Cli.JsonMapping].ok(_json_mapping({})),
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
        out = m.Cli.CommandOutput(exit_code=0, stdout="", stderr="")
        service = FlextInfraDependencyDetectionService()
        monkeypatch.setattr(
            u.Cli, "run_raw", _StubRunRaw(r[m.Cli.CommandOutput].ok(out))
        )
        monkeypatch.setattr(
            u.Cli,
            "toml_read_json",
            _StubTomlReadJson([
                r[t.Cli.JsonMapping].ok(_json_mapping({})),
                r[t.Cli.JsonMapping].ok(
                    _json_mapping({
                        "project": {"optional-dependencies": {"typings": []}},
                    })
                ),
            ]),
        )
        tm.ok(service.get_required_typings(tmp_path, venv_bin))
        monkeypatch.setattr(
            u.Cli,
            "toml_read_json",
            _StubTomlReadJson([
                r[t.Cli.JsonMapping].ok(_json_mapping({})),
                r[t.Cli.JsonMapping].ok(_json_mapping({})),
            ]),
        )
        tm.ok(service.get_required_typings(tmp_path, venv_bin, include_mypy=False))
        monkeypatch.setattr(
            u.Cli, "run_raw", _StubRunRaw(r[m.Cli.CommandOutput].fail("mypy crash"))
        )
        monkeypatch.setattr(
            u.Cli,
            "toml_read_json",
            _StubTomlReadJson([r[t.Cli.JsonMapping].ok(_json_mapping({}))]),
        )
        tm.fail(service.get_required_typings(tmp_path, venv_bin))
