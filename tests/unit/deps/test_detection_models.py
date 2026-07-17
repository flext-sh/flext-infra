from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from flext_tests import tm

from flext_infra import m, p, t
from flext_infra.deps.detection import FlextInfraDependencyDetectionService


class TestsFlextInfraDepsDetectionModels:
    def test_deptry_issue_groups_creation(self) -> None:
        groups = m.Infra.DeptryIssueGroups()
        tm.that(groups.dep001, eq=[])
        tm.that(groups.dep002, eq=[])
        tm.that(groups.dep003, eq=[])
        tm.that(groups.dep004, eq=[])

    def test_deptry_report_creation(self) -> None:
        report = m.Infra.DeptryReport(
            missing=[], unused=[], transitive=[], dev_in_runtime=[], raw_count=0
        )
        tm.that(report.missing, empty=True)
        tm.that(report.unused, empty=True)
        tm.that(report.transitive, empty=True)
        tm.that(report.dev_in_runtime, empty=True)
        tm.that(report.raw_count, eq=0)

    def test_project_dependency_report_creation(self) -> None:
        deptry = m.Infra.DeptryReport(
            missing=[], unused=[], transitive=[], dev_in_runtime=[], raw_count=0
        )
        report = m.Infra.ProjectDependencyReport(project="test-project", deptry=deptry)
        tm.that(report.project, eq="test-project")
        tm.that(report.deptry, eq=deptry)

    def test_typings_report_creation(self) -> None:
        report = m.Infra.TypingsReport(
            required_packages=[],
            hinted=[],
            missing_modules=[],
            current=[],
            to_add=[],
            to_remove=[],
        )
        tm.that(report.required_packages, empty=True)
        tm.that(report.hinted, empty=True)
        tm.that(report.missing_modules, empty=True)
        tm.that(report.current, empty=True)
        tm.that(report.to_add, empty=True)
        tm.that(report.to_remove, empty=True)
        tm.that(not report.limits_applied, eq=True)
        tm.that(report.python_version, eq=None)

    def test_service_initialization(self) -> None:
        FlextInfraDependencyDetectionService()

    def test_default_module_to_types_package_mapping(self) -> None:
        service = FlextInfraDependencyDetectionService()
        limits = service.load_dependency_limits()
        tm.that(service.module_to_types_package("yaml", limits), eq="types-pyyaml")

    def test_none_value(self) -> None:
        tm.that(FlextInfraDependencyDetectionService.to_infra_value(None), none=True)

    def test_string_value(self) -> None:
        tm.that(
            FlextInfraDependencyDetectionService.to_infra_value("hello"), eq="hello"
        )

    def test_int_value(self) -> None:
        tm.that(FlextInfraDependencyDetectionService.to_infra_value(42), eq=42)

    def test_float_value(self) -> None:
        tm.that(
            FlextInfraDependencyDetectionService.to_infra_value(math.pi), eq=math.pi
        )

    def test_bool_value(self) -> None:
        tm.that(FlextInfraDependencyDetectionService.to_infra_value(True), eq=True)

    def test_list_of_valid_values(self) -> None:
        tm.that(
            FlextInfraDependencyDetectionService.to_infra_value(["a", 1, True]),
            eq=["a", 1, True],
        )

    def test_list_with_unconvertible(self) -> None:
        assert (
            FlextInfraDependencyDetectionService.to_infra_value(
                cast("t.JsonValue", [Path("/tmp")])
            )
            is None
        )

    def test_mapping_value(self) -> None:
        result = FlextInfraDependencyDetectionService.to_infra_value({
            "key": "value",
            "num": 42,
        })
        tm.that(result, is_=Mapping)
        tm.that(result, eq={"key": "value", "num": 42})

    def test_mapping_with_unconvertible(self) -> None:
        assert (
            FlextInfraDependencyDetectionService.to_infra_value(
                cast("t.JsonValue", {"key": Path("/tmp")})
            )
            is None
        )

    def test_unsupported_type(self) -> None:
        assert (
            FlextInfraDependencyDetectionService.to_infra_value(
                cast("t.JsonValue", Path("/tmp"))
            )
            is None
        )

    def test_list_with_none_item(self) -> None:
        tm.that(
            FlextInfraDependencyDetectionService.to_infra_value([None, "a"]),
            eq=[None, "a"],
        )

    def test_mapping_with_none_value(self) -> None:
        result = FlextInfraDependencyDetectionService.to_infra_value({"key": None})
        tm.that(result, is_=Mapping)
        tm.that(result, eq={"key": None})
