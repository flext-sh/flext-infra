"""Detect deep imports that should use top-level aliases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import (
    DetectorContext,
    FlextInfraScanFileMixin,
    FlextInfraUtilitiesRope,
    c,
    m,
    p,
)


class FlextInfraImportAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect deep import paths that should use top-level aliases."""

    _rule_id: ClassVar[str] = "namespace.import_alias"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Deep import '{current_import}' should use '{suggested_import}'"
    )

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: DetectorContext,
    ) -> Sequence[m.Infra.ImportAliasViolation]:
        """Detect deep alias imports directly from Rope import descriptors."""
        file_path = ctx.file_path
        if file_path.name == c.Infra.Files.INIT_PY:
            return []
        resource = FlextInfraUtilitiesRope.get_resource_from_path(
            ctx.rope_project,
            file_path,
        )
        if resource is None:
            return []
        source = resource.read()
        if cls._looks_like_facade_file(file_path=file_path, source=source):
            return []
        source_lines = source.splitlines()
        violations: list[m.Infra.ImportAliasViolation] = []
        for from_import in FlextInfraUtilitiesRope.get_absolute_from_imports(
            ctx.rope_project,
            resource,
        ):
            if not cls._is_deep_flext_module(from_import.module_name):
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
                    line=cls._find_import_line(
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

    @staticmethod
    def _is_deep_flext_module(module_name: str) -> bool:
        if not module_name.startswith("flext_") or "." not in module_name:
            return False
        return all(not part.startswith("_") for part in module_name.split(".")[1:])

    @staticmethod
    def _looks_like_facade_file(*, file_path: Path, source: str) -> bool:
        from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing

        return FlextInfraUtilitiesParsing.looks_like_facade_file(
            file_path=file_path, source=source
        )

    @staticmethod
    def _find_import_line(*, lines: Sequence[str], module_name: str) -> int:
        from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing

        return FlextInfraUtilitiesParsing.find_import_line(
            lines=lines, module_name=module_name
        )


__all__ = ["FlextInfraImportAliasDetector"]
