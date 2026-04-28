from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService, r
from tests import u


class TestsFlextInfraDepsDetectionTypingsFlow:
    def test_module_to_types_package(self) -> None:
        service = FlextInfraDependencyDetectionService()
        tm.that(service.module_to_types_package("yaml", {}), eq="types-pyyaml")
        tm.that(service.module_to_types_package("flext_core", {}), eq=None)
        tm.that(
            service.module_to_types_package(
                "yaml",
                {
                    "typing_libraries": {
                        "module_to_package": {"yaml": "custom-types-yaml"},
                    },
                },
            ),
            eq="custom-types-yaml",
        )
        tm.that(service.module_to_types_package("unknown_module", {}), eq=None)
        tm.that(service.module_to_types_package("yaml.parser", {}), eq="types-pyyaml")

    def test_get_current_typings_from_pyproject(self) -> None:
        service = FlextInfraDependencyDetectionService()
        service.toml = u.Tests.TomlReaderSequence(
            [
                u.Tests.infra_mapping_result(
                    {
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
                    },
                ),
            ],
        )

        got = service.get_current_typings_from_pyproject(Path("/dummy"))

        tm.that(got, empty=True)

    def test_get_current_typings_from_pyproject_variants(self) -> None:
        service = FlextInfraDependencyDetectionService()
        service.toml = u.Tests.TomlReaderSequence(
            [
                u.Tests.infra_mapping_result(
                    {
                        "project": {
                            "optional-dependencies": {
                                "typings": [
                                    "types-pyyaml>=6.0",
                                    "types-requests[extra]==2.28",
                                ],
                            },
                        },
                    },
                ),
                u.Tests.infra_mapping_result(
                    {
                        "project": {
                            "optional-dependencies": {
                                "typings": {"types-pyyaml": ">=6.0"},
                            },
                        },
                    },
                ),
                r.fail("not found"),
                u.Tests.infra_mapping_result({}),
            ],
        )
        path = Path("/dummy")

        tm.that(service.get_current_typings_from_pyproject(path), empty=True)
        tm.that(service.get_current_typings_from_pyproject(path), empty=True)
        tm.that(service.get_current_typings_from_pyproject(path), empty=True)
        tm.that(service.get_current_typings_from_pyproject(path), empty=True)

    def test_get_required_typings_paths(self, tmp_path: Path) -> None:
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        _ = (venv_bin / "mypy").write_text("", encoding="utf-8")
        command_output = u.Tests.create_command_output()
        service = u.Tests.create_deptry_service(command_output=command_output)
        service.toml = u.Tests.TomlReaderSequence(
            [
                u.Tests.infra_mapping_result({}),
                u.Tests.infra_mapping_result(
                    {
                        "project": {"optional-dependencies": {"typings": []}},
                    },
                ),
            ],
        )
        tm.ok(service.get_required_typings(tmp_path, venv_bin))

        service.toml = u.Tests.TomlReaderSequence(
            [
                u.Tests.infra_mapping_result({}),
                u.Tests.infra_mapping_result({}),
            ],
        )
        tm.ok(service.get_required_typings(tmp_path, venv_bin, include_mypy=False))

        failing_service = u.Tests.create_deptry_service(run_error="mypy crash")
        failing_service.toml = u.Tests.TomlReaderSequence(
            [u.Tests.infra_mapping_result({})],
        )
        tm.fail(failing_service.get_required_typings(tmp_path, venv_bin))
