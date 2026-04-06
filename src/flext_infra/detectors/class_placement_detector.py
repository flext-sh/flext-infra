"""Detect Pydantic model classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraScanFileMixin, c, m, p, t, u


class FlextInfraClassPlacementDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect Pydantic models outside canonical model files via rope."""

    _rule_id: ClassVar[str] = "namespace.class_placement"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Model class '{name}' must be in canonical model files ({suggestion})"
    )

    @staticmethod
    def _normalize_base_name(base_name: str) -> str:
        """Normalize semantic/AST base names to their terminal class name."""
        return base_name.rsplit(".", maxsplit=1)[-1]

    @classmethod
    def _matching_base_class(cls, base_names: t.StrSequence) -> str | None:
        """Return the first supported Pydantic base class found in base_names."""
        for base_name in base_names:
            normalized = cls._normalize_base_name(base_name)
            if normalized in c.Infra.ClassPlacement.PYDANTIC_BASE_NAMES:
                return normalized
        return None

    @classmethod
    def _ast_class_info(
        cls,
        rope_project: t.Infra.RopeProject,
        file_path: Path,
    ) -> Mapping[str, m.Infra.ClassInfo]:
        """Parse class declarations when rope cannot resolve imported base classes."""
        source = cls._get_source_or_empty(rope_project, file_path)
        if source is None:
            return {}
        return {ci.name: ci for ci in u.Infra.parse_all_class_bases(source)}

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.ClassPlacementViolation]:
        """Detect misplaced Pydantic model classes."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        if (
            file_path.name in c.Infra.ClassPlacement.CANONICAL_MODEL_FILES
            or "_models" in file_path.parts
            or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
            or file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        ast_class_info = cls._ast_class_info(rope_project, file_path)
        rope_class_info = list(u.Infra.get_class_info(rope_project, res))
        processed_names = {ci.name for ci in rope_class_info}
        class_info = [
            *rope_class_info,
            *[
                info
                for name, info in ast_class_info.items()
                if name not in processed_names
            ],
        ]
        violations: list[m.Infra.ClassPlacementViolation] = []
        for ci in class_info:
            if ci.name.startswith("_"):
                continue
            base_class = cls._matching_base_class(ci.bases)
            if base_class is None:
                ast_info = ast_class_info.get(ci.name)
                if ast_info is None:
                    continue
                base_class = cls._matching_base_class(ast_info.bases)
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
