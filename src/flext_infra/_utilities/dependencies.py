"""Dependency parsing and inspection helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r
from flext_infra._utilities.pyproject import (
    FlextInfraUtilitiesPyproject,
    _validate_infra_payload,
)
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraUtilitiesDependencies:
    """Static helpers for inspecting dependency declarations in pyproject payloads."""

    @staticmethod
    def dep_name(requirement: str) -> str | None:
        """Extract normalized dependency name from one requirement spec."""
        text = requirement.strip()
        if not text:
            return None
        if ";" in text:
            text = text.split(";", maxsplit=1)[0].strip()
        if " @ " in text:
            text = text.split(" @ ", maxsplit=1)[0].strip()
        for separator in ("[", "==", ">=", "<=", "~=", "!=", ">", "<"):
            if separator in text:
                text = text.split(separator, maxsplit=1)[0].strip()
        if "/" in text:
            text = text.rsplit("/", maxsplit=1)[-1].strip()
        normalized = text.lower()
        return normalized or None

    @staticmethod
    def constraint_specifier(version: str) -> str:
        """Return the resolved lock version as an open-ended dependency floor."""
        normalized_version = version.strip()
        return f">={normalized_version}" if normalized_version else ""

    @classmethod
    def locked_dependency_state(
        cls, lock_path: Path
    ) -> p.Result[m.Infra.DependencyLockState]:
        """Return one validated inventory without conflating Git-only and invalid."""
        if not lock_path.is_file():
            return r[m.Infra.DependencyLockState].fail(
                f"dependency lock does not exist: {lock_path}"
            )
        try:
            raw_text = lock_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        except OSError as exc:
            return r[m.Infra.DependencyLockState].fail_op("read dependency lock", exc)
        payload_source = u.Cli.toml_mapping_from_text(raw_text)
        payload = (
            _validate_infra_payload(payload_source)
            if payload_source is not None
            else None
        )
        if payload is None:
            return r[m.Infra.DependencyLockState].fail(
                f"invalid dependency lock TOML: {lock_path}"
            )
        raw_packages = payload.get("package")
        if not isinstance(raw_packages, list):
            return r[m.Infra.DependencyLockState].fail(
                f"dependency lock has no package inventory: {lock_path}"
            )
        package_names: set[str] = set()
        registry_versions: dict[str, str] = {}
        for raw_package in raw_packages:
            if not isinstance(raw_package, Mapping):
                return r[m.Infra.DependencyLockState].fail(
                    f"dependency lock contains an invalid package entry: {lock_path}"
                )
            raw_name = raw_package.get("name")
            raw_source = raw_package.get("source")
            dependency_name = (
                cls.dep_name(raw_name) if isinstance(raw_name, str) else None
            )
            if dependency_name is None or not isinstance(raw_source, Mapping):
                return r[m.Infra.DependencyLockState].fail(
                    f"dependency lock contains incomplete package metadata: {lock_path}"
                )
            package_names.add(dependency_name)
            if "registry" not in raw_source:
                continue
            raw_version = raw_package.get(c.Infra.VERSION)
            if not isinstance(raw_version, str) or not raw_version.strip():
                return r[m.Infra.DependencyLockState].fail(
                    f"registry package lacks a locked version: {dependency_name}"
                )
            registry_versions[dependency_name] = raw_version.strip()
        return r[m.Infra.DependencyLockState].ok(
            m.Infra.DependencyLockState(
                package_names=tuple(sorted(package_names)),
                registry_versions=dict(registry_versions),
            )
        )

    @classmethod
    def locked_dependency_versions(cls, lock_path: Path) -> t.MappingKV[str, str]:
        """Return normalized registry versions while preserving the legacy API."""
        state_result = cls.locked_dependency_state(lock_path)
        return {} if state_result.failure else state_result.value.registry_versions

    @staticmethod
    def requirement_uses_direct_source(requirement: str) -> bool:
        """Return whether one PEP 621 requirement uses a direct reference."""
        requirement_part, _separator, _marker = requirement.strip().partition(";")
        return " @ " in requirement_part

    @staticmethod
    def poetry_dependency_uses_direct_source(raw_value: t.Infra.InfraValue) -> bool:
        """Return whether one Poetry value declares a non-registry source."""
        return isinstance(raw_value, Mapping) and any(
            key in raw_value for key in (c.Infra.PATH, "git", "url")
        )

    @classmethod
    def rewrite_requirement_constraint(
        cls,
        requirement: str,
        *,
        locked_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence = (),
    ) -> str | None:
        """Rewrite one PEP 621 requirement to the resolved uv.lock floor."""
        result: str | None = None
        raw_text = requirement.strip()
        if raw_text:
            requirement_part, marker_separator, marker_part = raw_text.partition(";")
            if not cls.requirement_uses_direct_source(raw_text):
                head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(
                    requirement_part.strip()
                )
                if head_match is not None:
                    head = head_match.group("head").strip()
                    dependency_name = cls.dep_name(head)
                    internal_set = set(internal_names)
                    if (
                        dependency_name is not None
                        and dependency_name not in internal_set
                    ):
                        locked_version = locked_versions.get(dependency_name)
                        if locked_version is not None:
                            rewritten = (
                                f"{head}{cls.constraint_specifier(locked_version)}"
                            )
                            marker_text = marker_part.strip()
                            if marker_separator and marker_text:
                                rewritten = f"{rewritten}; {marker_text}"
                            result = rewritten if rewritten != raw_text else None
        return result

    @classmethod
    def rewrite_poetry_constraint(
        cls,
        dependency_name: str,
        raw_value: t.Infra.InfraValue,
        *,
        locked_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence = (),
    ) -> t.Infra.InfraValue | None:
        """Rewrite one Poetry dependency to the resolved uv.lock floor."""
        result: t.Infra.InfraValue | None = None
        normalized_name = cls.dep_name(dependency_name)
        internal_set = set(internal_names)
        if (
            normalized_name is not None
            and normalized_name != "python"
            and normalized_name not in internal_set
        ):
            locked_version = locked_versions.get(normalized_name)
            if locked_version is not None:
                rewritten_specifier = cls.constraint_specifier(locked_version)
                if isinstance(raw_value, str):
                    result = (
                        rewritten_specifier
                        if raw_value != rewritten_specifier
                        else None
                    )
                elif isinstance(
                    raw_value, Mapping
                ) and not cls.poetry_dependency_uses_direct_source(raw_value):
                    updated: t.MutableJsonMapping = dict(raw_value)
                    if updated.get(c.Infra.VERSION) != rewritten_specifier:
                        updated[c.Infra.VERSION] = rewritten_specifier
                        result = dict(updated)
        return result

    @staticmethod
    def dedupe_specs(specs: t.StrSequence) -> t.StrSequence:
        """Return deterministic unique dependency specs keyed by normalized name."""
        selected_by_name: dict[str, str] = {}
        for raw in specs:
            item = raw.strip()
            if not item:
                continue
            dependency_name = FlextInfraUtilitiesDependencies.dep_name(item)
            if dependency_name is None or dependency_name in selected_by_name:
                continue
            selected_by_name[dependency_name] = item
        return tuple(selected_by_name[name] for name in sorted(selected_by_name))

    @classmethod
    def declared_dependency_names(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
        """Return normalized dependency names from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.declared_dependency_names_from_payload(normalized)

    @classmethod
    def declared_dependency_names_from_payload(
        cls, payload: t.JsonMapping
    ) -> t.StrSequence:
        """Return normalized dependency names across supported dependency tables."""
        return tuple(
            declaration.name
            for declaration in cls.dependency_declarations_from_payload(payload)
        )

    @classmethod
    def dependency_declarations_from_payload(
        cls, payload: t.JsonMapping
    ) -> t.SequenceOf[m.Infra.DependencyDeclaration]:
        """Enumerate every dependency once and aggregate its registry contract."""
        requirement_groups: t.MutableSequenceOf[t.Infra.InfraValue] = []
        poetry_tables: t.MutableSequenceOf[t.Infra.InfraValue] = []
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, Mapping):
            requirement_groups.append(project.get(c.Infra.DEPENDENCIES))
            optional_dependencies = project.get(c.Infra.OPTIONAL_DEPENDENCIES)
            if isinstance(optional_dependencies, Mapping):
                requirement_groups.extend(optional_dependencies.values())
        dependency_groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if isinstance(dependency_groups, Mapping):
            requirement_groups.extend(dependency_groups.values())
        tool = payload.get(c.Infra.TOOL)
        poetry = tool.get(c.Infra.POETRY) if isinstance(tool, Mapping) else None
        if isinstance(poetry, Mapping):
            poetry_tables.append(poetry.get(c.Infra.DEPENDENCIES))
            poetry_groups = poetry.get(c.Infra.GROUP)
            if isinstance(poetry_groups, Mapping):
                poetry_tables.extend(
                    raw_group.get(c.Infra.DEPENDENCIES)
                    for raw_group in poetry_groups.values()
                    if isinstance(raw_group, Mapping)
                )
        registry_required_by_name: dict[str, bool] = {}
        for raw_requirements in requirement_groups:
            if not isinstance(raw_requirements, list):
                continue
            for raw_requirement in raw_requirements:
                requirement = str(raw_requirement)
                dependency_name = cls.dep_name(requirement)
                if dependency_name is None:
                    continue
                registry_required_by_name[dependency_name] = (
                    registry_required_by_name.get(dependency_name, False)
                    or not cls.requirement_uses_direct_source(requirement)
                )
        for raw_mapping in poetry_tables:
            if not isinstance(raw_mapping, Mapping):
                continue
            for raw_name, raw_value in raw_mapping.items():
                dependency_name = cls.dep_name(raw_name)
                if dependency_name is None or dependency_name == "python":
                    continue
                registry_required_by_name[dependency_name] = (
                    registry_required_by_name.get(dependency_name, False)
                    or not cls.poetry_dependency_uses_direct_source(raw_value)
                )
        return tuple(
            m.Infra.DependencyDeclaration(
                name=dependency_name,
                registry_required=registry_required_by_name[dependency_name],
            )
            for dependency_name in sorted(registry_required_by_name)
        )

    @classmethod
    def dependency_requires_registry_lock_from_payload(
        cls, payload: t.JsonMapping, dependency_name: str
    ) -> bool:
        """Return whether any selected declaration expects a registry version."""
        selected_name = cls.dep_name(dependency_name)
        if selected_name is None:
            return False
        return next(
            (
                declaration.registry_required
                for declaration in cls.dependency_declarations_from_payload(payload)
                if declaration.name == selected_name
            ),
            False,
        )

    @classmethod
    def local_dependency_names_from_payload(
        cls, payload: t.JsonMapping, *, workspace_project_names: t.StrSequence = ()
    ) -> t.StrSequence:
        """Return workspace-local dependency names from one payload."""
        declared = set(cls.declared_dependency_names_from_payload(payload))
        if not workspace_project_names:
            return ()
        workspace_names = set(workspace_project_names)
        return tuple(sorted(name for name in declared if name in workspace_names))

    @staticmethod
    def project_dev_groups_from_payload(
        payload: t.JsonMapping,
    ) -> t.MappingKV[str, t.StrSequence]:
        """Collect optional dependency groups from one normalized payload."""
        project = u.Cli.json_as_mapping(payload.get(c.Infra.PROJECT, None))
        optional = u.Cli.json_as_mapping(
            project.get(c.Infra.OPTIONAL_DEPENDENCIES, None)
        )
        groups = {
            str(group): tuple(
                str(item) for item in u.Cli.json_as_sequence(optional.get(group, None))
            )
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
        }
        return {group: values for group, values in groups.items() if values}

    @classmethod
    def project_dev_groups(
        cls, document: t.Cli.TomlDocument
    ) -> t.MappingKV[str, t.StrSequence]:
        """Collect optional dependency groups from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            # mro-j47u (codex): keep the empty mapping immutable and fully typed.
            return MappingProxyType(dict[str, tuple[str, ...]]())
        return cls.project_dev_groups_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.canonical_dev_dependencies_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies_from_payload(
        cls, payload: t.JsonMapping
    ) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one normalized payload."""
        groups = cls.project_dev_groups_from_payload(payload)
        return cls.dedupe_specs([
            requirement
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
            for requirement in groups.get(str(group), ())
        ])

    @classmethod
    def flext_dependency_namespaces(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract declared FLEXT dependency namespaces from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.flext_dependency_namespaces_from_payload(normalized)

    @classmethod
    def flext_dependency_namespaces_from_payload(
        cls, payload: t.MappingKV[str, t.Infra.InfraValue]
    ) -> t.StrSequence:
        """Extract every declared ``flext-*`` dependency as a Python namespace."""
        # mro-j47u (codex): FLEXT dependencies are first-party contracts even
        # when their uv source declaration is owned by an enclosing workspace.
        normalized = _validate_infra_payload(payload)
        if normalized is None:
            return ()
        return tuple(
            sorted(
                name.replace("-", "_")
                for name in cls.declared_dependency_names_from_payload(normalized)
                if name == "flext" or name.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesDependencies"]
