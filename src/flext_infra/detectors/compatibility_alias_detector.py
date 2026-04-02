"""Detect removable compatibility alias assignments via source scan.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from flext_infra import DetectorContext, FlextInfraScanFileMixin, c, m, p


class FlextInfraCompatibilityAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect compatibility alias assignments (CapName = CapName)."""

    _rule_id: ClassVar[str] = "namespace.compatibility_alias"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Compatibility alias '{alias_name}' -> '{target_name}'"
    )

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: DetectorContext,
    ) -> Sequence[m.Infra.CompatibilityAliasViolation]:
        """Detect compatibility aliases in a single file."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        if file_path.suffix != ".py":
            return []
        source = cls._get_source_or_empty(rope_project, file_path)
        if source is None:
            return []
        violations: list[m.Infra.CompatibilityAliasViolation] = []
        for hit in c.Infra.COMPAT_ALIAS_RE.finditer(source):
            alias_name, target_name = hit.group(1), hit.group(2)
            if alias_name in c.Infra.COMPAT_SKIP_NAMES or alias_name == target_name:
                continue
            if alias_name.isupper() and target_name.isupper():
                continue
            line = source[: hit.start()].count("\n") + 1
            violations.append(
                m.Infra.CompatibilityAliasViolation(
                    file=str(file_path),
                    line=line,
                    alias_name=alias_name,
                    target_name=target_name,
                )
            )
        return violations


__all__ = ["FlextInfraCompatibilityAliasDetector"]
