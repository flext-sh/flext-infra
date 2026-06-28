"""Detect loose top-level objects outside namespace classes via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import (
    c,
    m,
    t,
    u,
)


class FlextInfraLooseObjectDetector:
    """Detect loose top-level objects outside namespace classes via rope."""

    @classmethod
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect loose top-level objects in a single file."""
        res = u.Infra.fetch_python_resource(
            ctx.rope_project,
            ctx.file_path,
            skip_protected=True,
            skip_settings=True,
            skip_alias_modules=True,
            skip_init_py=True,
        )
        if res is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        project_name = ctx.project_name
        lines = res.read().splitlines()
        class_stem = m.derive_class_stem(project_name)
        file_str = str(file_path)
        violations = list(
            cls._detect_logger_assignments(
                lines=lines,
                file_str=file_str,
                class_stem=class_stem,
            )
        )
        logger_keys = {
            (violation.line, violation.name)
            for violation in violations
            if violation.kind == "logger"
        }

        def _add(symbol: m.Infra.SymbolInfo, kind: str, suffix: str) -> None:
            """Add."""
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=symbol.line,
                    name=symbol.name,
                    kind=kind,
                    suggestion=f"{class_stem}{suffix}",
                )
            )

        class_symbols: t.MutableSequenceOf[m.Infra.SymbolInfo] = []
        for symbol in u.Infra.get_module_symbols(rope_project, res):
            if (symbol.line, symbol.name) in logger_keys:
                continue
            if symbol.name in c.Infra.SCAN_ALLOWED_TOP_LEVEL:
                continue
            if symbol.kind == "class":
                if symbol.name in c.Infra.DETECTION_CANONICAL_ALIASES:
                    continue
                class_symbols.append(symbol)
                continue
            if symbol.kind == "function":
                _add(symbol, "function", "Utilities")
                continue
            line = lines[symbol.line - 1] if 0 < symbol.line <= len(lines) else ""
            if line.lstrip().startswith("type "):
                _add(symbol, "typealias", "Types")
                continue
            if (
                symbol.kind == "assignment"
                and len(symbol.name) > c.Infra.NAMESPACE_MIN_ALIAS_LENGTH
                and not symbol.name.startswith("_")
                and c.Infra.NAMESPACE_CONSTANT_PATTERN.match(symbol.name)
            ):
                _add(symbol, "constant", "Constants")

        if len(class_symbols) != 1:
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=1,
                    name=file_path.stem,
                    kind="single_class",
                    suggestion=f"{class_stem}Utilities",
                )
            )

        return violations

    @staticmethod
    def _detect_logger_assignments(
        *,
        lines: t.StrSequence,
        file_str: str,
        class_stem: str,
    ) -> t.SequenceOf[m.Infra.LooseObjectViolation]:
        """Detect top-level logger assignments directly from module source."""
        return tuple(
            m.Infra.LooseObjectViolation(
                file=file_str,
                line=line_number,
                name=match.group(1),
                kind="logger",
                suggestion=f"{class_stem}Utilities",
            )
            for line_number, line in enumerate(lines, start=1)
            if (match := c.Infra.LOGGER_ASSIGN_RE.match(line))
        )


__all__: list[str] = ["FlextInfraLooseObjectDetector"]
