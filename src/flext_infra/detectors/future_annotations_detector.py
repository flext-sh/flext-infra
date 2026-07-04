"""Detect missing 'from __future__ import annotations' via source scan.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraFutureAnnotationsDetector:
    """Detect missing future annotations import via rope resource read."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.FutureAnnotationsViolation]:
        """Detect missing future annotations in a single file."""
        resource = u.Infra.fetch_python_resource(
            ctx.rope_project,
            ctx.file_path,
            skip_protected=True,
        )
        if resource is None:
            return []
        file_path = ctx.file_path
        source = resource.read()
        if not source.strip():
            return []
        if c.Infra.ONLY_DOCSTRING_RE.match(source.strip()):
            return []
        if c.Infra.FUTURE_ANNOTATIONS_RE.search(source):
            return []
        return [m.Infra.FutureAnnotationsViolation(file=str(file_path))]


__all__: list[str] = ["FlextInfraFutureAnnotationsDetector"]
