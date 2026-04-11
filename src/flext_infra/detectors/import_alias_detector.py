"""Detect deep imports that should use top-level aliases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import (
    c,
    m,
    u,
)


class FlextInfraImportAliasDetector:
    """Detect deep import paths that should use top-level aliases."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.ImportAliasViolation]:
        """Detect deep alias imports directly from Rope import descriptors."""
        file_path = ctx.file_path
        if file_path.name == c.Infra.INIT_PY:
            return []
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
        violations: list[m.Infra.ImportAliasViolation] = []
        for from_import in u.Infra.get_absolute_from_imports(
            ctx.rope_project,
            resource,
        ):
            if not (
                from_import.module_name.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
                and "." in from_import.module_name
                and all(
                    not part.startswith("_")
                    for part in from_import.module_name.split(".")[1:]
                )
            ):
                continue
            alias_names = sorted(
                name
                for name, alias in from_import.names_and_aliases
                if alias is None and name in c.Infra.RUNTIME_ALIAS_NAMES
            )
            if not alias_names:
                continue
            current_import = (
                f"from {from_import.module_name} import {', '.join(alias_names)}"
            )
            root_module = from_import.module_name.split(".", maxsplit=1)[0]
            violations.append(
                m.Infra.ImportAliasViolation(
                    file=str(file_path),
                    line=u.Infra.find_import_line(
                        lines=source_lines,
                        module_name=from_import.module_name,
                    ),
                    current_import=current_import,
                    suggested_import=(
                        f"from {root_module} import {', '.join(alias_names)}"
                    ),
                )
            )
        return violations


__all__ = ["FlextInfraImportAliasDetector"]
