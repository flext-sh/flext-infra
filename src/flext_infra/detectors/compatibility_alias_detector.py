"""Detect removable compatibility alias assignments via source scan.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)

from flext_infra import c, m, u


class FlextInfraCompatibilityAliasDetector:
    """Detect compatibility alias assignments (CapName = CapName)."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.CompatibilityAliasViolation]:
        """Detect compatibility aliases in a single file."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        lines = resource.read().splitlines()
        violations: list[m.Infra.CompatibilityAliasViolation] = []
        for symbol in u.Infra.get_module_symbols(rope_project, resource):
            if symbol.kind != "assignment" or not 0 < symbol.line <= len(lines):
                continue
            match = c.Infra.COMPAT_ALIAS_RE.match(lines[symbol.line - 1])
            if match is None:
                continue
            alias_name, target_name = match.group(1), match.group(2)
            if alias_name in c.Infra.COMPAT_SKIP_NAMES or alias_name == target_name:
                continue
            if alias_name.isupper() and target_name.isupper():
                continue
            violations.append(
                m.Infra.CompatibilityAliasViolation(
                    file=str(file_path),
                    line=symbol.line,
                    alias_name=alias_name,
                    target_name=target_name,
                )
            )
        return violations


__all__: list[str] = ["FlextInfraCompatibilityAliasDetector"]
