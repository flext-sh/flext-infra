"""Dependency detection and analysis service for deptry and pip-check.

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

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.deps import FlextInfraDepsDetectionRunners


class FlextInfraDependencyDetectionService(FlextInfraDepsDetectionRunners):
    """Runtime vs dev dependency detector using deptry and pip-check."""

    _log = u.fetch_logger(__name__)

    @staticmethod
    def classify_issues(
        issues: Sequence[t.JsonMapping],
    ) -> m.Infra.DeptryIssueGroups:
        """Classify deptry issues by error code (DEP001-DEP004).

        Returns:
            The resulting ``m.Infra.DeptryIssueGroups``.

        """
        groups = m.Infra.DeptryIssueGroups(dep001=[], dep002=[], dep003=[], dep004=[])
        for item in issues:
            normalized_item: MutableMapping[str, t.Primitives | None] = {}
            for key, raw_value in item.items():
                if raw_value is None:
                    normalized_item[key] = ""
                    continue
                if isinstance(raw_value, c.PRIMITIVES_TYPES):
                    normalized_item[key] = raw_value
            error_obj = item.get(c.Infra.ERROR)
            if not isinstance(error_obj, Mapping):
                continue
            error_data = u.Cli.json_as_mapping(error_obj)
            if not error_data:
                continue
            code = error_data.get(c.Infra.CODE)
            bucket = {
                "DEP001": groups.dep001,
                "DEP002": groups.dep002,
                "DEP003": groups.dep003,
                "DEP004": groups.dep004,
            }.get(str(code) if code is not None else "")
            if bucket is not None:
                bucket.append(normalized_item)
        return groups

    def build_project_report(
        self,
        project_name: str,
        deptry_issues: Sequence[t.JsonMapping],
    ) -> m.Infra.ProjectDependencyReport:
        """Build a project dependency report from classified deptry issues.

        Returns:
            The project's native dependency report, retained through serialization.

        """
        classified = self.classify_issues(deptry_issues)

        def _module_names(
            items: Sequence[Mapping[str, t.JsonValue | None]],
        ) -> MutableSequence[str]:
            """Extract module names from classified issue items.

            Returns:
                The resulting ``MutableSequence[str]``.

            """
            return [
                str(val)
                for item in items
                if (val := item.get(c.Infra.MODULE)) is not None
            ]

        return m.Infra.ProjectDependencyReport(
            project=project_name,
            deptry=m.Infra.DeptryReport(
                missing=_module_names(classified.dep001),
                unused=_module_names(classified.dep002),
                transitive=_module_names(classified.dep003),
                dev_in_runtime=_module_names(classified.dep004),
                raw_count=len(deptry_issues),
            ),
        )

    @staticmethod
    def discover_project_paths(
        repository_root: Path,
        projects_filter: Sequence[str] | None = None,
    ) -> p.Result[Sequence[Path]]:
        """Discover project paths with pyproject.toml in workspace.

        Returns only the Path objects, filtered to those with pyproject.toml.
        For full ProjectInfo metadata, use u.Infra.discover_projects().

        Returns:
            The resulting ``p.Result[Sequence[Path]]``.

        """
        names = projects_filter or []
        result = u.Infra.resolve_projects(repository_root, names)
        if result.failure:
            return r[Sequence[Path]].from_failure(result)
        projects_info: Sequence[m.Infra.ProjectInfo] = result.value
        projects = [
            project.path
            for project in projects_info
            if (project.path / c.PYPROJECT_FILENAME).exists()
        ]
        return r[Sequence[Path]].ok(sorted(projects))


__all__: list[str] = ["FlextInfraDependencyDetectionService"]
