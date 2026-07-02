"""Detect classes declared outside their canonical family locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, t, u


class FlextInfraClassPlacementDetector:
    """Detect misplaced class declarations across the five FLEXT families."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.ClassPlacementViolation]:
        """Detect classes that belong in a different family directory/file."""
        if u.Infra.matches_root_namespace_file(ctx.file_path.name):
            return []
        res = u.Infra.fetch_python_resource(
            ctx.rope_project,
            ctx.file_path,
            skip_protected=True,
            skip_settings=True,
        )
        if res is None:
            return []
        file_path = ctx.file_path
        parts = file_path.parts
        violations: list[m.Infra.ClassPlacementViolation] = []
        for ci in u.Infra.get_class_info(ctx.rope_project, res):
            name = ci.name
            if name.startswith("_"):
                continue
            family = FlextInfraClassPlacementDetector._family_for_class(ci)
            if family is None:
                continue
            if FlextInfraClassPlacementDetector._in_canonical_location(
                family,
                parts,
                file_path.name,
            ):
                continue
            target = FlextInfraClassPlacementDetector._suggestion_for_family(family)
            violations.append(
                m.Infra.ClassPlacementViolation(
                    file=str(file_path),
                    line=ci.line,
                    name=name,
                    base_class=ci.bases[0] if ci.bases else "",
                    suggestion=target,
                ),
            )
        return violations

    @staticmethod
    def _family_for_class(
        ci: m.Infra.ClassInfo,
    ) -> str | None:
        """Return the canonical family letter for a class, or None if not governed."""
        terminal_bases = {
            base_name.rsplit(".", maxsplit=1)[-1] for base_name in ci.bases
        }
        if terminal_bases & c.Infra.PLACEMENT_PYDANTIC_BASE_NAMES:
            return "m"
        if terminal_bases & c.Infra.PLACEMENT_PROTOCOL_BASE_NAMES:
            return "p"
        if terminal_bases & c.Infra.PLACEMENT_ENUM_BASE_NAMES:
            return "c"
        if any(
            ci.name.endswith(suffix)
            for suffix in c.Infra.PLACEMENT_UTILITY_NAME_SUFFIXES
        ):
            return "u"
        return None

    @staticmethod
    def _in_canonical_location(
        family: str,
        parts: tuple[str, ...],
        file_name: str,
    ) -> bool:
        """Return True when the file already lives in the canonical family area."""
        dir_sets = {
            "m": c.Infra.PLACEMENT_CANONICAL_MODEL_DIRS,
            "p": c.Infra.PLACEMENT_CANONICAL_PROTOCOL_DIRS,
            "c": c.Infra.PLACEMENT_CANONICAL_CONSTANTS_DIRS,
            "u": c.Infra.PLACEMENT_CANONICAL_UTILITY_DIRS,
        }
        file_sets = {
            "m": c.Infra.PLACEMENT_CANONICAL_MODEL_FILES,
            "p": c.Infra.PLACEMENT_CANONICAL_PROTOCOL_FILES,
            "c": c.Infra.PLACEMENT_CANONICAL_CONSTANTS_FILES,
            "u": c.Infra.PLACEMENT_CANONICAL_UTILITY_FILES,
        }
        if file_name in file_sets.get(family, frozenset()):
            return True
        return bool(set(parts) & dir_sets.get(family, frozenset()))

    @staticmethod
    def _suggestion_for_family(family: str) -> str:
        """Return a human-readable relocation suggestion for a family."""
        return {
            "m": "Move Pydantic model class to models.py or _models/",
            "p": "Move Protocol class to protocols.py or _protocols/",
            "c": "Move Enum constant class to constants.py or _constants/",
            "u": "Move utility class to utilities.py or _utilities/",
        }.get(family, "Move class to canonical family location")


__all__: list[str] = ["FlextInfraClassPlacementDetector"]
