from __future__ import annotations

from collections.abc import Mapping, Sequence

from flext_core import FlextUtilities

from flext_infra import FlextInfraUtilitiesCodegenTransforms, c, t


class FlextInfraCodegenCoercion(FlextInfraUtilitiesCodegenTransforms):
    @staticmethod
    def as_int(value: t.Infra.InfraValue) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    @staticmethod
    def dict_or_empty(value: t.Infra.InfraValue) -> Mapping[str, t.Infra.InfraValue]:
        if not FlextUtilities.is_mapping(value):
            return {}
        return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)

    @staticmethod
    def dict_list(
        value: t.Infra.InfraValue,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        if not isinstance(value, list):
            return []
        result: Sequence[Mapping[str, t.Infra.InfraValue]] = [
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item)
            for item in value
            if FlextUtilities.is_mapping(item)
        ]
        return result

    @staticmethod
    def extract_total_violations(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "total_violations" in payload:
            return FlextInfraCodegenCoercion.as_int(payload.get("total_violations"))
        totals = FlextInfraCodegenCoercion.dict_or_empty(payload.get("totals"))
        if totals:
            return (
                FlextInfraCodegenCoercion.as_int(totals.get("ns001_violations"))
                + FlextInfraCodegenCoercion.as_int(totals.get("layer_violations"))
                + FlextInfraCodegenCoercion.as_int(
                    totals.get("cross_project_reference_violations"),
                )
            )
        projects = FlextInfraCodegenCoercion.dict_list(payload.get("projects"))
        if projects and all("total" in item for item in projects):
            return sum(
                FlextInfraCodegenCoercion.as_int(item.get("total")) for item in projects
            )
        return -1

    @staticmethod
    def extract_duplicate_groups(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        if "duplicate_groups" in payload:
            return FlextInfraCodegenCoercion.as_int(payload.get("duplicate_groups"))
        duplicates = payload.get("duplicates")
        if isinstance(duplicates, list):
            return sum(1 for _ in duplicates)
        return -1

    @staticmethod
    def extract_projects_total(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraCodegenCoercion.dict_or_empty(payload.get("totals"))
        value = totals.get(c.Infra.ReportKeys.PROJECTS)
        if value is not None:
            return FlextInfraCodegenCoercion.as_int(value)
        projects = payload.get("projects")
        if isinstance(projects, list):
            return sum(1 for _ in projects)
        return 0

    @staticmethod
    def extract_projects_passed(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraCodegenCoercion.dict_or_empty(payload.get("totals"))
        return FlextInfraCodegenCoercion.as_int(totals.get("passed"))

    @staticmethod
    def extract_projects_failed(payload: Mapping[str, t.Infra.InfraValue]) -> int:
        totals = FlextInfraCodegenCoercion.dict_or_empty(payload.get("totals"))
        return FlextInfraCodegenCoercion.as_int(totals.get("failed"))


__all__ = ["FlextInfraCodegenCoercion"]
