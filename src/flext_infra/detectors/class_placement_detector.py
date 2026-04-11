"""Detect Pydantic model classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import c, m, u


class FlextInfraClassPlacementDetector:
    """Detect Pydantic models outside canonical model files via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.ClassPlacementViolation]:
        """Detect misplaced Pydantic model classes."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        if (
            file_path.name in c.Infra.PLACEMENT_CANONICAL_MODEL_FILES
            or "_models" in file_path.parts
            or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
            or file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        violations: list[m.Infra.ClassPlacementViolation] = []
        for ci in u.Infra.get_class_info(rope_project, res):
            if ci.name.startswith("_"):
                continue
            base_class = next(
                (
                    base_name.rsplit(".", maxsplit=1)[-1]
                    for base_name in ci.bases
                    if base_name.rsplit(".", maxsplit=1)[-1]
                    in c.Infra.PLACEMENT_PYDANTIC_BASE_NAMES
                ),
                None,
            )
            if base_class is None:
                continue
            violations.append(
                m.Infra.ClassPlacementViolation(
                    file=str(file_path),
                    line=ci.line,
                    name=ci.name,
                    base_class=base_class,
                    suggestion="Move class to models.py/_models.py or _models/",
                ),
            )
        return violations


__all__ = ["FlextInfraClassPlacementDetector"]
