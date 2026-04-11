"""Detect alias imports from wrong source packages.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import (
    c,
    m,
    u,
)


class FlextInfraNamespaceSourceDetector:
    """Detect alias imports from wrong source packages."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        """Detect runtime aliases imported from a different flext package root."""
        file_path = ctx.file_path
        project_root = ctx.project_root
        if project_root is None or file_path.name == c.Infra.INIT_PY:
            return []
        package_name = u.Infra.package_name(project_root)
        if not package_name:
            return []
        local_aliases = (
            FlextInfraNamespaceSourceDetector._discover_local_runtime_aliases(
                project_root=project_root, package_name=package_name
            )
        )
        if not local_aliases:
            return []
        contextual_sources = u.Infra.contextual_runtime_alias_sources(
            project_root=project_root,
            file_path=file_path,
            rope_project=ctx.rope_project,
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
            if current_source == package_name or current_source.startswith(
                f"{package_name}."
            ):
                continue
            if not (
                current_source.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
                and "." not in current_source
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
            project_root / c.Infra.DEFAULT_SRC_DIR / package_name / c.Infra.INIT_PY
        )
        return set(c.Infra.RUNTIME_ALIAS_NAMES) if init_path.is_file() else set()


__all__ = ["FlextInfraNamespaceSourceDetector"]
