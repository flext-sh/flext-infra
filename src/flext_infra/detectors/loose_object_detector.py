"""Detect loose top-level objects outside namespace classes via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence

from flext_infra import (
    FlextInfraUtilitiesCodegenNamespace,
    c,
    m,
    u,
)


class FlextInfraLooseObjectDetector:
    """Detect loose top-level objects outside namespace classes via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.LooseObjectViolation]:
        """Detect loose top-level objects in a single file."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        project_name = ctx.project_name
        if (
            file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
            or file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        lines = res.read().splitlines()
        class_stem = FlextInfraUtilitiesCodegenNamespace.project_class_stem(
            project_name=project_name,
        )
        file_str = str(file_path)
        violations: MutableSequence[m.Infra.LooseObjectViolation] = []

        def _add(symbol: m.Infra.SymbolInfo, kind: str, suffix: str) -> None:
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=symbol.line,
                    name=symbol.name,
                    kind=kind,
                    suggestion=f"{class_stem}{suffix}",
                )
            )

        for symbol in u.Infra.get_module_symbols(rope_project, res):
            if symbol.kind == "class" or symbol.name in c.Infra.SCAN_ALLOWED_TOP_LEVEL:
                continue
            if symbol.kind == "function":
                if not symbol.name.startswith("_"):
                    _add(symbol, "function", "Utilities")
                continue
            line = lines[symbol.line - 1] if 0 < symbol.line <= len(lines) else ""
            if line.lstrip().startswith("type "):
                _add(symbol, "typealias", "Types")
                continue
            if c.Infra.LOGGER_ASSIGN_RE.match(line):
                _add(symbol, "logger", "Utilities")
                continue
            if (
                symbol.kind == "assignment"
                and len(symbol.name) > c.Infra.NAMESPACE_MIN_ALIAS_LENGTH
                and not symbol.name.startswith("_")
                and c.Infra.NAMESPACE_CONSTANT_PATTERN.match(symbol.name)
            ):
                _add(symbol, "constant", "Constants")

        return violations


__all__: list[str] = ["FlextInfraLooseObjectDetector"]
