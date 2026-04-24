"""Project classification and family chain discovery for flext workspace."""

from __future__ import annotations

import re
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
)
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraProjectClassifier:
    """Classify a project by kind and discover MRO family chains."""

    def __init__(
        self,
        project_root: Path,
        *,
        pyproject_payload: t.Infra.ContainerDict | None = None,
    ) -> None:
        """Initialize classifier for the given project root."""
        self._project_root = project_root.resolve()
        self._pyproject_path = self._project_root / c.Infra.PYPROJECT_FILENAME
        self._pyproject_payload = pyproject_payload
        self._src_path = self._project_root / c.Infra.DEFAULT_SRC_DIR

    def classify(self) -> m.Infra.ProjectClassification:
        """Return classification and family chains for this project."""
        project_name, dependencies = self._read_project_metadata()
        internal_dependencies = self._internal_dependencies(
            dependencies=dependencies,
            project_name=project_name,
        )
        family_bases, local_facade_classes = self._discover_facade_inheritance()
        family_chains = self._build_confirmed_family_chains(
            internal_dependencies=internal_dependencies,
            family_bases=family_bases,
        )
        project_kind = self._infer_project_kind(
            internal_dependencies=internal_dependencies,
            local_facade_classes=local_facade_classes,
        )
        return m.Infra.ProjectClassification(
            project_kind=project_kind,
            family_chains={**family_chains},
        )

    def _read_project_metadata(self) -> t.Infra.TransformResult:
        if self._pyproject_payload is not None:
            return self._project_metadata_from_payload(self._pyproject_payload)
        empty_dependencies: list[str] = []
        if not self._pyproject_path.is_file():
            return ("", empty_dependencies)
        data_result = u.Cli.toml_read_json(self._pyproject_path)
        if data_result.failure:
            return ("", empty_dependencies)
        return self._project_metadata_from_payload(
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(data_result.value),
        )

    def _project_metadata_from_payload(
        self,
        parsed: t.Infra.ContainerDict,
    ) -> t.Infra.TransformResult:
        raw_project = self._as_mapping(parsed.get(c.Infra.PROJECT))
        project_name = self._normalized_name_from_mapping(raw_project)
        dependencies: MutableSequence[str] = []
        self._append_project_dependencies(
            raw_project=raw_project,
            dependencies=dependencies,
        )
        raw_tool = self._as_mapping(parsed.get(c.Infra.TOOL))
        raw_poetry = self._as_mapping(raw_tool.get(c.Infra.POETRY))
        if not project_name:
            project_name = self._normalized_name_from_mapping(raw_poetry)
        self._append_poetry_dependencies(
            raw_poetry=raw_poetry,
            dependencies=dependencies,
        )
        return (project_name, dependencies)

    def _as_mapping(
        self,
        raw_value: t.Infra.InfraValue | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        if isinstance(raw_value, Mapping):
            validated: Mapping[
                str, t.Infra.InfraValue
            ] = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw_value)
            return validated
        return {}

    def _normalized_name_from_mapping(
        self,
        raw_mapping: Mapping[str, t.Infra.InfraValue],
    ) -> str:
        raw_name = raw_mapping.get(c.Infra.NAME)
        if isinstance(raw_name, str):
            return self._normalize_dependency_name(raw_name)
        return ""

    def _append_project_dependencies(
        self,
        *,
        raw_project: Mapping[str, t.Infra.InfraValue],
        dependencies: MutableSequence[str],
    ) -> None:
        raw_dependencies = raw_project.get(c.Infra.DEPENDENCIES)
        if not isinstance(raw_dependencies, list):
            return
        for raw_dependency in raw_dependencies:
            if not isinstance(raw_dependency, str):
                continue
            dependency_name = self._extract_dependency_name(raw_dependency)
            self._append_unique_dependency(
                dependency_name=dependency_name,
                dependencies=dependencies,
            )

    def _append_poetry_dependencies(
        self,
        *,
        raw_poetry: Mapping[str, t.Infra.InfraValue],
        dependencies: MutableSequence[str],
    ) -> None:
        self._append_poetry_dependency_mapping(
            raw_mapping=self._as_mapping(raw_poetry.get(c.Infra.DEPENDENCIES)),
            dependencies=dependencies,
        )
        raw_group = self._as_mapping(raw_poetry.get(c.Infra.GROUP))
        raw_test_group = self._as_mapping(raw_group.get(c.Infra.TEST))
        self._append_poetry_dependency_mapping(
            raw_mapping=self._as_mapping(raw_test_group.get(c.Infra.DEPENDENCIES)),
            dependencies=dependencies,
        )

    def _append_poetry_dependency_mapping(
        self,
        *,
        raw_mapping: Mapping[str, t.Infra.InfraValue],
        dependencies: MutableSequence[str],
    ) -> None:
        dependency_keys = self._ordered_mapping_keys(raw_mapping)
        for dependency_key in dependency_keys:
            dependency_name = self._extract_dependency_name(dependency_key)
            if dependency_name == "python":
                continue
            self._append_unique_dependency(
                dependency_name=dependency_name,
                dependencies=dependencies,
            )

    def _ordered_mapping_keys(
        self,
        raw_mapping: Mapping[str, t.Infra.InfraValue],
    ) -> t.StrSequence:
        keys = list(raw_mapping.keys())
        if self._mapping_order_is_trusted(raw_mapping):
            return keys
        return sorted(keys)

    def _mapping_order_is_trusted(
        self,
        raw_mapping: Mapping[str, t.Infra.InfraValue],
    ) -> bool:
        return isinstance(raw_mapping, dict)

    def _append_unique_dependency(
        self,
        *,
        dependency_name: str,
        dependencies: MutableSequence[str],
    ) -> None:
        if (not dependency_name) or (dependency_name in dependencies):
            return
        dependencies.append(dependency_name)

    def _internal_dependencies(
        self,
        *,
        dependencies: t.StrSequence,
        project_name: str,
    ) -> t.StrSequence:
        return [
            dependency
            for dependency in dependencies
            if dependency.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            and dependency != project_name
        ]

    def _extract_dependency_name(self, raw_dependency: str) -> str:
        cleaned = raw_dependency.strip().split(";", maxsplit=1)[0].strip()
        if not cleaned:
            return ""
        left_side = cleaned.split(" @ ", maxsplit=1)[0].strip()
        base_token = left_side.split()[0]
        base_token = base_token.split("[", maxsplit=1)[0]
        base_token = re.split(r"[<>=!~]", base_token, maxsplit=1)[0]
        if "/" in base_token:
            path = Path(base_token)
            base_token = path.name
        return self._normalize_dependency_name(base_token)

    def _normalize_dependency_name(self, raw_name: str) -> str:
        normalized = u.norm_str(raw_name, case="lower").replace("_", "-")
        return normalized.strip("./")

    def _discover_facade_inheritance(
        self,
    ) -> t.Infra.Pair[Mapping[str, t.Infra.StrSet], t.Infra.StrSet]:
        family_bases: Mapping[str, t.Infra.StrSet] = {
            family: set() for family in c.Infra.FAMILY_SUFFIXES
        }
        local_facade_classes: t.Infra.StrSet = set()
        if not self._src_path.is_dir():
            return (family_bases, local_facade_classes)
        for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
            file_pattern = c.Infra.FAMILY_FILES[family]
            for file_path in self._src_path.rglob(file_pattern):
                class_bases, class_names = self._parse_family_file(file_path, suffix)
                family_bases[family].update(class_bases)
                local_facade_classes.update(class_names)
        return (family_bases, local_facade_classes)

    _CLASS_DEF_RE: t.Infra.RegexPattern = c.Infra.CLASS_WITH_BASES_RE

    def _parse_family_file(
        self,
        file_path: Path,
        suffix: str,
    ) -> t.Infra.Pair[t.Infra.StrSet, t.Infra.StrSet]:
        try:
            source = file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        except (OSError, UnicodeDecodeError):
            return (set(), set())
        base_names: t.Infra.StrSet = set()
        class_names: t.Infra.StrSet = set()
        for match in self._CLASS_DEF_RE.finditer(source):
            name = match.group(1)
            if not name.endswith(suffix):
                continue
            class_names.add(name)
            bases_str = match.group(2)
            for base_part in bases_str.split(","):
                base_part = base_part.strip()
                if not base_part:
                    continue
                base_name = base_part.split("[")[0].rsplit(".", maxsplit=1)[-1].strip()
                if base_name:
                    base_names.add(base_name)
        return (base_names, class_names)

    def _build_confirmed_family_chains(
        self,
        *,
        internal_dependencies: t.StrSequence,
        family_bases: Mapping[str, t.Infra.StrSet],
    ) -> Mapping[str, t.StrSequence]:
        family_chains: MutableMapping[str, t.StrSequence] = {}
        for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
            expected_parents = self._expected_parents_for_family(
                family_suffix=suffix,
                internal_dependencies=internal_dependencies,
            )
            confirmed_bases = family_bases.get(family, set())
            confirmed_expected = [
                parent for parent in expected_parents if parent in confirmed_bases
            ]
            extra_confirmed = sorted(
                base for base in confirmed_bases if base not in set(confirmed_expected)
            )
            family_chains[family] = [*confirmed_expected, *extra_confirmed]
        return family_chains

    def _expected_parents_for_family(
        self,
        *,
        family_suffix: str,
        internal_dependencies: t.StrSequence,
    ) -> t.StrSequence:
        expected: MutableSequence[str] = []
        for dependency in internal_dependencies:
            stem = self._dependency_to_class_stem(dependency)
            if not stem:
                continue
            candidate = f"{stem}{family_suffix}"
            if candidate not in expected:
                expected.append(candidate)
        return expected

    def _dependency_to_class_stem(self, dependency: str) -> str:
        normalized = self._normalize_dependency_name(dependency)
        if normalized == c.Infra.PKG_CORE:
            return "Flext"
        if normalized.startswith(c.Infra.PKG_PREFIX_HYPHEN):
            tail = normalized.removeprefix(c.Infra.PKG_PREFIX_HYPHEN)
            parts = [part for part in tail.split("-") if part]
            if not parts:
                return ""
            return "Flext" + "".join(part.capitalize() for part in parts)
        parts = [part for part in normalized.split("-") if part]
        if not parts:
            return ""
        return "".join(part.capitalize() for part in parts)

    def _infer_project_kind(
        self,
        *,
        internal_dependencies: t.StrSequence,
        local_facade_classes: t.Infra.StrSet,
    ) -> str:
        if not internal_dependencies:
            return "core"
        has_domain_dependency = any(
            dependency in c.Infra.DOMAIN_PACKAGES
            for dependency in internal_dependencies
        )
        has_platform_dependency = any(
            dependency in c.Infra.PLATFORM_PACKAGES
            for dependency in internal_dependencies
        )
        dependency_kind = "app"
        if has_domain_dependency and has_platform_dependency:
            dependency_kind = "integration"
        elif has_domain_dependency:
            dependency_kind = "domain"
        elif has_platform_dependency:
            dependency_kind = "platform"
        has_integration_facade = any(
            class_name.startswith(c.Infra.INTEGRATION_CLASS_PREFIXES)
            for class_name in local_facade_classes
        )
        if dependency_kind == "integration" and (not has_integration_facade):
            return "app"
        if (
            dependency_kind == "app"
            and has_domain_dependency
            and has_platform_dependency
            and has_integration_facade
        ):
            return "integration"
        return dependency_kind


__all__: list[str] = ["FlextInfraProjectClassifier"]
