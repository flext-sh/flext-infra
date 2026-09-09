"""Typing declarations are read from real PEP 621 and PEP 735 source."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c
from flext_infra.deps.detection import FlextInfraDependencyDetectionService


class TestsFlextInfraDepsDetectionTypingsFlow:
    def test_module_to_types_package(self) -> None:
        service = FlextInfraDependencyDetectionService()
        tm.that(service.module_to_types_package("yaml", {}), eq=None)
        tm.that(service.module_to_types_package("flext_core", {}), eq=None)
        tm.that(service.module_to_types_package("unknown_module", {}), eq=None)
        tm.that(service.module_to_types_package("yaml.parser", {}), eq=None)
        tm.that(
            service.module_to_types_package(
                "yaml",
                {
                    "typing_libraries": {
                        "module_to_package": {"yaml": "custom-types-yaml"}
                    }
                },
            ),
            eq="custom-types-yaml",
        )

    def test_custom_typings_and_managed_dev_are_both_available(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "typed-reader"\n'
            "[project.optional-dependencies]\n"
            'typings = ["types-pyyaml>=6.0", "types-requests[extra]==2.28"]\n'
            'feature = ["feature-only"]\n'
            '[dependency-groups]\ndev = ["types-python-dateutil", "pytest"]\n',
            encoding="utf-8",
        )
        service = FlextInfraDependencyDetectionService()
        tm.that(
            service.get_current_typings_from_pyproject(tmp_path),
            eq=["pytest", "types-python-dateutil", "types-pyyaml", "types-requests"],
        )
        tm.that(
            service.get_current_typings_from_pyproject(tmp_path, include_dev=False),
            eq=["types-pyyaml", "types-requests"],
        )
        limits = tmp_path / "limits.toml"
        limits.write_text("[typing_libraries]\n", encoding="utf-8")
        report = tm.ok(
            service.get_required_typings(tmp_path, limits, include_mypy=False)
        )
        tm.that(report.to_remove, eq=["types-pyyaml", "types-requests"])
        tm.that(report.to_add, empty=True)

    def test_retired_poetry_typings_are_not_a_source(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[tool.poetry.group.typings.dependencies]\ntypes-requests = "*"\n',
            encoding="utf-8",
        )
        tm.that(
            FlextInfraDependencyDetectionService().get_current_typings_from_pyproject(
                tmp_path
            ),
            empty=True,
        )

    def test_invalid_typings_table_fails_at_ingress(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project.optional-dependencies.typings]\ntypes-requests = "*"\n',
            encoding="utf-8",
        )
        with pytest.raises(c.ValidationError):
            FlextInfraDependencyDetectionService().get_current_typings_from_pyproject(
                tmp_path
            )

    def test_absent_pyproject_has_no_declarations(self, tmp_path: Path) -> None:
        tm.that(
            FlextInfraDependencyDetectionService().get_current_typings_from_pyproject(
                tmp_path
            ),
            empty=True,
        )

    @pytest.mark.parametrize("requirement", ["", " "])
    def test_blank_typing_requirement_is_rejected(
        self, tmp_path: Path, requirement: str
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            f'[project.optional-dependencies]\ntypings = ["{requirement}"]\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="must not be blank"):
            FlextInfraDependencyDetectionService().get_current_typings_from_pyproject(
                tmp_path
            )

    def test_malformed_pyproject_preserves_read_failure(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[broken", encoding="utf-8")
        with pytest.raises(RuntimeError, match="failed to read"):
            FlextInfraDependencyDetectionService().get_current_typings_from_pyproject(
                tmp_path
            )
