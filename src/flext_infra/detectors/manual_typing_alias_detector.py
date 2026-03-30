"""Detect type aliases outside canonical typings locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraScanFileMixin, c, m, p, t

_PEP695_RE = c.Infra.PEP695_RE
_TYPEALIAS_ANNOT_RE = c.Infra.TYPEALIAS_ANNOT_RE


class FlextInfraManualTypingAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect type aliases outside canonical typings files via rope."""

    _rule_id: ClassVar[str] = "namespace.manual_typing_alias"
    _MESSAGE_TEMPLATE: ClassVar[str] = "Typing alias '{name}': {detail}"

    @classmethod
    @override
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
        project_name: str = "",
        project_root: Path | None = None,
    ) -> Sequence[m.Infra.ManualTypingAliasViolation]:
        """Detect type alias placement violations in a single file."""
        del parse_failures, project_name, project_root
        if (
            file_path.suffix != ".py"
            or file_path.name in c.Infra.MRO_TYPINGS_FILE_NAMES
            or c.Infra.MRO_TYPINGS_DIRECTORY in file_path.parts
        ):
            return []
        source = cls._get_source_or_empty(rope_project, file_path)
        if source is None:
            return []
        violations: MutableSequence[m.Infra.ManualTypingAliasViolation] = []
        # PEP 695: type Foo = ...
        for hit in _PEP695_RE.finditer(source):
            violations.append(
                m.Infra.ManualTypingAliasViolation(
                    file=str(file_path),
                    line=source[: hit.start()].count("\n") + 1,
                    name=hit.group(1),
                    detail="PEP695 alias must be centralized under typings scope",
                )
            )
        # TypeAlias annotation: Foo: TypeAlias = ...
        for hit in _TYPEALIAS_ANNOT_RE.finditer(source):
            violations.append(
                m.Infra.ManualTypingAliasViolation(
                    file=str(file_path),
                    line=source[: hit.start()].count("\n") + 1,
                    name=hit.group(1),
                    detail="TypeAlias assignment must be centralized under typings scope",
                )
            )
        return violations


__all__ = ["FlextInfraManualTypingAliasDetector"]
