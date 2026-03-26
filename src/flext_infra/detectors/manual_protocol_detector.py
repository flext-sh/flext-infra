"""Detect Protocol classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import FlextInfraScanFileMixin, c, m, p, t, u


class FlextInfraManualProtocolDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect Protocol classes outside canonical protocol files via rope."""

    _rule_id: ClassVar[str] = "namespace.manual_protocol"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Protocol class '{name}' must be centralized ({suggestion})"
    )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ManualProtocolViolation]:
        """Detect Protocol classes outside canonical locations."""
        del parse_failures
        if (
            file_path.name in c.Infra.NAMESPACE_CANONICAL_PROTOCOL_FILES
            or c.Infra.NAMESPACE_CANONICAL_PROTOCOL_DIR in file_path.parts
            or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        return [
            m.Infra.ManualProtocolViolation.create(
                file=str(file_path), line=ci.line, name=ci.name
            )
            for ci in u.Infra.get_class_info(rope_project, res)
            if "Protocol" in ci.bases
        ]


__all__ = ["FlextInfraManualProtocolDetector"]
