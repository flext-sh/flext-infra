"""Detect missing 'from __future__ import annotations' via source scan.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import FlextInfraScanFileMixin, c, m, p, t, u

_FUTURE_ANNOTATIONS_RE = c.Infra.FUTURE_ANNOTATIONS_RE
_ONLY_DOCSTRING_RE = c.Infra.ONLY_DOCSTRING_RE


class FlextInfraFutureAnnotationsDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect missing future annotations import via rope resource read."""

    _rule_id: ClassVar[str] = "namespace.future_annotations"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Missing 'from __future__ import annotations'"
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
        source = cls._get_source_or_empty(rope_project, file_path)
        if source is None:
            return []
        if not source.strip():
            return []
        if _ONLY_DOCSTRING_RE.match(source.strip()):
            return []
        if _FUTURE_ANNOTATIONS_RE.search(source):
            return []
        return [m.Infra.FutureAnnotationsViolation.create(file=str(file_path))]


__all__ = ["FlextInfraFutureAnnotationsDetector"]
