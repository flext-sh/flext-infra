"""Detect loose typing declarations outside canonical typings locations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence

from flext_infra import c, m, u


class FlextInfraManualTypingAliasDetector:
    """Detect typing declarations outside canonical typings files via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.ManualTypingAliasViolation]:
        """Detect typing declaration placement violations in a single file."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        if (
            file_path.suffix != c.Infra.EXT_PYTHON
            or file_path.name in c.Infra.MRO_TYPINGS_FILE_NAMES
            or c.Infra.MRO_TYPINGS_DIRECTORY in file_path.parts
        ):
            return []
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            return []
        lines = resource.read().splitlines()
        violations: MutableSequence[m.Infra.ManualTypingAliasViolation] = []
        for symbol in u.Infra.get_module_symbols(rope_project, resource):
            if symbol.kind != "assignment" or not 0 < symbol.line <= len(lines):
                continue
            line = lines[symbol.line - 1]
            detail = ""
            if line.lstrip().startswith("type "):
                detail = "PEP695 alias must be centralized under typings scope"
            elif c.Infra.TYPEALIAS_ANNOT_RE.match(line):
                detail = "TypeAlias assignment must be centralized under typings scope"
            elif c.Infra.TYPING_FACTORY_ASSIGN_RE.match(line):
                detail = (
                    "Typing factory assignment must be centralized under typings scope"
                )
            if detail:
                violations.append(
                    m.Infra.ManualTypingAliasViolation(
                        file=str(file_path),
                        line=symbol.line,
                        name=symbol.name,
                        detail=detail,
                    )
                )
        return violations


__all__ = ["FlextInfraManualTypingAliasDetector"]
