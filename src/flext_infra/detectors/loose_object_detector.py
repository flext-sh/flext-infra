"""Detect loose top-level objects outside namespace classes via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import (
    DetectorContext,
    FlextInfraNamespaceFacadeScanner,
    FlextInfraScanFileMixin,
    c,
    m,
    p,
    t,
    u,
)

_CONSTANT_RE = c.Infra.NAMESPACE_CONSTANT_PATTERN
_ALLOWED_TOP_LEVEL: frozenset[str] = frozenset({
    c.Infra.Dunders.ALL,
    c.Infra.Dunders.VERSION,
    "__version_info__",
})

_FUNC_DEF_RE = c.Infra.FUNC_DEF_RE
_ASSIGN_RE = c.Infra.ASSIGN_RE
_TYPE_ALIAS_RE = c.Infra.PEP695_RE


class FlextInfraLooseObjectDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect loose top-level objects outside namespace classes via rope."""

    _rule_id: ClassVar[str] = "namespace.loose_object"
    _MESSAGE_TEMPLATE: ClassVar[str] = "Loose {kind} '{name}' outside namespace"

    def __init__(
        self,
        *,
        project_name: str,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize with project name and mandatory rope project."""
        super().__init__(rope_project=rope_project, parse_failures=parse_failures)
        self._project_name = project_name

    @override
    def _collect_violations(
        self, file_path: Path
    ) -> Sequence[m.Infra.LooseObjectViolation]:
        return self.detect_file(
            DetectorContext(
                file_path=file_path,
                project_name=self._project_name,
                rope_project=self._rope,
                parse_failures=self._pf,
            ),
        )

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: DetectorContext,
    ) -> Sequence[m.Infra.LooseObjectViolation]:
        """Detect loose top-level objects in a single file."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        project_name = ctx.project_name
        if (
            file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
            or file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES
        ):
            return []
        res = u.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        source: str = res.read()
        class_stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        # Get all classes defined in module (these are NOT loose)
        known_classes = set(u.get_module_classes(rope_project, res))

        file_str = str(file_path)
        violations: MutableSequence[m.Infra.LooseObjectViolation] = []

        def _add(hit: re.Match[str], name: str, kind: str, suffix: str) -> None:
            violations.append(
                m.Infra.LooseObjectViolation(
                    file=file_str,
                    line=source.count("\n", 0, hit.start()) + 1,
                    name=name,
                    kind=kind,
                    suggestion=f"{class_stem}{suffix}",
                )
            )

        for hit in _FUNC_DEF_RE.finditer(source):
            name = hit.group(2)
            if not name.startswith("_"):
                _add(hit, name, "function", "Utilities")

        for hit in _ASSIGN_RE.finditer(source):
            name = hit.group(1)
            if (
                name not in _ALLOWED_TOP_LEVEL
                and name not in known_classes
                and len(name) > c.Infra.NAMESPACE_MIN_ALIAS_LENGTH
                and not name.startswith("_")
                and _CONSTANT_RE.match(name)
            ):
                _add(hit, name, "constant", "Constants")

        for hit in _TYPE_ALIAS_RE.finditer(source):
            name = hit.group(1)
            if name not in _ALLOWED_TOP_LEVEL:
                _add(hit, name, "typealias", "Types")

        return violations


__all__ = ["FlextInfraLooseObjectDetector"]
