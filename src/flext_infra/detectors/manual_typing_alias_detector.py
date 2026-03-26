"""Detect type aliases outside canonical typings locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import FlextInfraScanFileMixin, c, m, p, t, u

_PEP695_RE = c.Infra.PEP695_RE
_TYPEALIAS_ANNOT_RE = c.Infra.TYPEALIAS_ANNOT_RE


class FlextInfraManualTypingAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect type aliases outside canonical typings files via rope."""

    _rule_id: ClassVar[str] = "namespace.manual_typing_alias"

    @override
    def _build_message(self, violation: BaseModel) -> str:
        d = violation.model_dump()
        return f"Typing alias '{d['name']}': {d['detail']}"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        return self.detect_file(
            file_path=file_path, rope_project=self._rope, parse_failures=self._pf
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ManualTypingAliasViolation]:
        """Detect type alias placement violations in a single file."""
        del parse_failures
        if (
            file_path.suffix != ".py"
            or file_path.name in c.Infra.NAMESPACE_CANONICAL_TYPINGS_FILES
            or c.Infra.NAMESPACE_CANONICAL_TYPINGS_DIR in file_path.parts
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        source = res.read()
        violations: MutableSequence[m.Infra.ManualTypingAliasViolation] = []
        # PEP 695: type Foo = ...
        for hit in _PEP695_RE.finditer(source):
            violations.append(
                m.Infra.ManualTypingAliasViolation.create(
                    file=str(file_path),
                    line=source[: hit.start()].count("\n") + 1,
                    name=hit.group(1),
                    detail="PEP695 alias must be centralized under typings scope",
                )
            )
        # TypeAlias annotation: Foo: TypeAlias = ...
        for hit in _TYPEALIAS_ANNOT_RE.finditer(source):
            violations.append(
                m.Infra.ManualTypingAliasViolation.create(
                    file=str(file_path),
                    line=source[: hit.start()].count("\n") + 1,
                    name=hit.group(1),
                    detail="TypeAlias assignment must be centralized under typings scope",
                )
            )
        return violations


__all__ = ["FlextInfraManualTypingAliasDetector"]
