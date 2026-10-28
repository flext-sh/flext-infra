"""Project dependency-list parsing (PEP 621 + poetry) — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, t, u


class FlextInfraRefactorProjectClassifierDeps:
    """Collect + normalize a project's declared dependency names.

    Composed into FlextInfraProjectClassifier via inheritance; owns the
    mapping boundary shared by metadata and dependency parsing.
    """

    def _append_project_dependencies(
        self,
        *,
        raw_project: Mapping[str, t.JsonValue],
        dependencies: MutableSequence[str],
    ) -> None:
        """Append project dependencies."""
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
        raw_poetry: Mapping[str, t.JsonValue],
        dependencies: MutableSequence[str],
    ) -> None:
        """Append poetry dependencies."""
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

    @staticmethod
    def _as_mapping(
        raw_value: t.JsonValue | None,
    ) -> Mapping[str, t.JsonValue]:
        """Validate one metadata mapping at the shared parsing boundary.

        Returns:
            The validated mapping, or an empty mapping for a non-mapping value.

        """
        if isinstance(raw_value, Mapping):
            validated: Mapping[str, t.JsonValue] = (
                t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw_value)
            )
            return validated
        return {}

    def _append_poetry_dependency_mapping(
        self,
        *,
        raw_mapping: Mapping[str, t.JsonValue],
        dependencies: MutableSequence[str],
    ) -> None:
        """Append poetry dependency mapping."""
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
        raw_mapping: Mapping[str, t.JsonValue],
    ) -> Sequence[str]:
        """Ordered mapping keys.

        Returns:
            The resulting ``Sequence[str]``.

        """
        keys = list(raw_mapping.keys())
        if self._mapping_order_is_trusted(raw_mapping):
            return keys
        return sorted(keys)

    @staticmethod
    def _mapping_order_is_trusted(
        raw_mapping: Mapping[str, t.JsonValue],
    ) -> bool:
        """Check whether the mapping order is trusted.

        Returns:
            The resulting ``bool``.

        """
        return isinstance(raw_mapping, dict)

    @staticmethod
    def _append_unique_dependency(
        *,
        dependency_name: str,
        dependencies: MutableSequence[str],
    ) -> None:
        """Append unique dependency."""
        if (not dependency_name) or (dependency_name in dependencies):
            return
        dependencies.append(dependency_name)

    @staticmethod
    def _internal_dependencies(
        *,
        dependencies: Sequence[str],
        project_name: str,
    ) -> Sequence[str]:
        """Return the internal dependencies.

        Returns:
            The internal dependencies.

        """
        return [
            dependency
            for dependency in dependencies
            if dependency.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            and dependency != project_name
        ]

    def _extract_dependency_name(self, raw_dependency: str) -> str:
        """Extract dependency name.

        Returns:
            The resulting ``str``.

        """
        cleaned = raw_dependency.strip().split(";", maxsplit=1)[0].strip()
        if not cleaned:
            return ""
        left_side = cleaned.split(" @ ", maxsplit=1)[0].strip()
        base_token = left_side.split()[0]
        base_token = base_token.split("[", maxsplit=1)[0]
        base_token = c.Infra.DEPENDENCY_VERSION_OP_RE.split(base_token, maxsplit=1)[0]
        if "/" in base_token:
            path = Path(base_token)
            base_token = path.name
        return self._normalize_dependency_name(base_token)

    @staticmethod
    def _normalize_dependency_name(raw_name: str) -> str:
        """Normalize dependency name.

        Returns:
            The resulting ``str``.

        """
        normalized: str = u.norm_str(raw_name, case="lower").replace("_", "-")
        return normalized.strip("./")


__all__: list[str] = ["FlextInfraRefactorProjectClassifierDeps"]
