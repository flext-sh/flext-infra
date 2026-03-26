"""Detect missing 'from __future__ import annotations' via source scan.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

from flext_infra import c, m, p, t, u

_FUTURE_ANNOTATIONS_RE = c.Infra.FUTURE_ANNOTATIONS_RE
_ONLY_DOCSTRING_RE = c.Infra.ONLY_DOCSTRING_RE


class FlextInfraFutureAnnotationsDetector(p.Infra.Scanner):
    """Detect missing future annotations import via rope resource read."""

    def __init__(
        self,
        *,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize with mandatory rope project."""
        super().__init__()
        self._rope = rope_project
        self._pf = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        violations = self.detect_file(
            file_path=file_path,
            rope_project=self._rope,
            parse_failures=self._pf,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=1,
                    message="Missing 'from __future__ import annotations'",
                    severity="error",
                    rule_id="namespace.future_annotations",
                )
                for _ in violations
            ],
            detector_name=self.__class__.__name__,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.FutureAnnotationsViolation]:
        """Detect missing future annotations in a single file."""
        del parse_failures
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        source = res.read()
        if not source.strip():
            return []
        if _ONLY_DOCSTRING_RE.match(source.strip()):
            return []
        if _FUTURE_ANNOTATIONS_RE.search(source):
            return []
        return [m.Infra.FutureAnnotationsViolation.create(file=str(file_path))]


__all__ = ["FlextInfraFutureAnnotationsDetector"]
