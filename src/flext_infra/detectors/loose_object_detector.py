"""Detect loose top-level objects outside namespace classes via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import (
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
    "__all__",
    "__version__",
    "__version_info__",
})

_FUNC_DEF_RE = c.Infra.FUNC_DEF_RE
_ASSIGN_RE = c.Infra.ASSIGN_RE
_TYPE_ALIAS_RE = c.Infra.TYPE_ALIAS_RE


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
    def _collect_violations(self, file_path: Path) -> Sequence[m.Infra.LooseObjectViolation]:
        return self.detect_file(
            file_path=file_path,
            project_name=self._project_name,
            rope_project=self._rope,
            parse_failures=self._pf,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        project_name: str,
        rope_project: t.Infra.RopeProject,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.LooseObjectViolation]:
        """Detect loose top-level objects in a single file."""
        del parse_failures
        if (
            file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
            or file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        source = res.read()
        class_stem = FlextInfraNamespaceFacadeScanner.project_class_stem(
            project_name=project_name,
        )
        # Get all classes defined in module (these are NOT loose)
        known_classes = set(u.Infra.get_module_classes(rope_project, res))

        violations: MutableSequence[m.Infra.LooseObjectViolation] = []

        # Detect loose functions (not dunder, not private)
        for hit in _FUNC_DEF_RE.finditer(source):
            name = hit.group(2)
            if name.startswith("__") and name.endswith("__"):
                continue
            if name.startswith("_"):
                continue
            line = source[: hit.start()].count("\n") + 1
            violations.append(
                m.Infra.LooseObjectViolation.create(
                    file=str(file_path),
                    line=line,
                    name=name,
                    kind="function",
                    suggestion=f"{class_stem}Utilities",
                )
            )

        # Detect loose constants (UPPER_CASE assignments)
        for hit in _ASSIGN_RE.finditer(source):
            name = hit.group(1)
            if name in _ALLOWED_TOP_LEVEL or name in known_classes:
                continue
            if len(name) <= c.Infra.NAMESPACE_MIN_ALIAS_LENGTH:
                continue
            if name.startswith("_"):
                continue
            if not _CONSTANT_RE.match(name):
                continue
            line = source[: hit.start()].count("\n") + 1
            violations.append(
                m.Infra.LooseObjectViolation.create(
                    file=str(file_path),
                    line=line,
                    name=name,
                    kind="constant",
                    suggestion=f"{class_stem}Constants",
                )
            )

        # Detect loose type aliases (PEP 695)
        for hit in _TYPE_ALIAS_RE.finditer(source):
            name = hit.group(1)
            if name not in _ALLOWED_TOP_LEVEL:
                line = source[: hit.start()].count("\n") + 1
                violations.append(
                    m.Infra.LooseObjectViolation.create(
                        file=str(file_path),
                        line=line,
                        name=name,
                        kind="typealias",
                        suggestion=f"{class_stem}Types",
                    )
                )

        return violations


__all__ = ["FlextInfraLooseObjectDetector"]
