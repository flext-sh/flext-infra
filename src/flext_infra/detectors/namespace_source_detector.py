"""Detect alias imports from wrong source packages.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import (
    FlextInfraScanFileMixin,
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraNamespaceSourceDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect alias imports from wrong source packages."""

    _rule_id: ClassVar[str] = "namespace.source_alias"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Wrong source for alias '{alias}': '{current_source}' -> '{correct_source}'"
    )

    def __init__(
        self,
        *,
        project_name: str,
        project_root: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize with project context and mandatory rope project."""
        super().__init__(rope_project=rope_project, parse_failures=parse_failures)
        self._project_name = project_name
        self._project_root = project_root

    @override
    def _collect_violations(
        self, file_path: Path
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        return self.detect_file(
            m.Infra.DetectorContext(
                file_path=file_path,
                project_name=self._project_name,
                project_root=self._project_root,
                rope_project=self._rope,
                parse_failures=self._pf,
            ),
        )

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        """Detect runtime aliases imported from a different flext package root."""
        file_path = ctx.file_path
        project_root = ctx.project_root
        if project_root is None or file_path.name == c.Infra.Files.INIT_PY:
            return []
        package_name = u.Infra.discover_project_package_name(project_root=project_root)
        if not package_name:
            return []
        local_aliases = cls._discover_local_runtime_aliases(
            project_root=project_root,
            package_name=package_name,
        )
        if not local_aliases:
            return []
        contextual_sources = u.Infra.contextual_runtime_alias_sources(
            project_root=project_root,
            file_path=file_path,
        )
        resource = u.Infra.get_resource_from_path(
            ctx.rope_project,
            file_path,
        )
        if resource is None:
            return []
        source = resource.read()
        if u.Infra.looks_like_facade_file(file_path=file_path, source=source):
            return []
        source_lines = source.splitlines()
        violations: list[m.Infra.NamespaceSourceViolation] = []
        for from_import in u.Infra.get_absolute_from_imports(
            ctx.rope_project,
            resource,
        ):
            current_source = from_import.module_name
            if not cls._is_candidate_wrong_source(
                current_source=current_source,
                package_name=package_name,
            ):
                continue
            wrong_aliases = sorted(
                name
                for name, alias in from_import.names_and_aliases
                if (
                    alias is None
                    and name in local_aliases
                    and name not in c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES
                    and current_source not in contextual_sources.get(name, frozenset())
                )
            )
            if not wrong_aliases:
                continue
            current_import = f"from {current_source} import {', '.join(wrong_aliases)}"
            line_number = u.Infra.find_import_line(
                lines=source_lines,
                module_name=current_source,
            )
            violations.extend(
                m.Infra.NamespaceSourceViolation(
                    file=str(file_path),
                    line=line_number,
                    alias=alias_name,
                    current_source=current_source,
                    correct_source=package_name,
                    current_import=current_import,
                    suggested_import=f"from {package_name} import {alias_name}",
                )
                for alias_name in wrong_aliases
            )
        return violations

    @staticmethod
    def _discover_local_runtime_aliases(
        *,
        project_root: Path,
        package_name: str,
    ) -> set[str]:
        init_path = (
            project_root
            / c.Infra.Paths.DEFAULT_SRC_DIR
            / package_name
            / c.Infra.Files.INIT_PY
        )
        return {
            alias_name
            for alias_name in u.Infra.extract_lazy_import_targets(init_path)
            if alias_name in c.Infra.RUNTIME_ALIAS_NAMES
        }

    @staticmethod
    def _is_candidate_wrong_source(
        *,
        current_source: str,
        package_name: str,
    ) -> bool:
        if current_source == package_name or current_source.startswith(
            f"{package_name}."
        ):
            return False
        return (
            current_source.startswith(c.Infra.Packages.PREFIX_UNDERSCORE)
            and "." not in current_source
        )


__all__ = ["FlextInfraNamespaceSourceDetector"]
