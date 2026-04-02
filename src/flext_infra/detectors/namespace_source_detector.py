"""Detect alias imports from wrong source packages.

Delegates to ImportNormalizerTransformer for CST-based detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import DetectorContext, FlextInfraScanFileMixin, c, m, p, t


class FlextInfraNamespaceSourceDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect alias imports from wrong source packages."""

    _rule_id: ClassVar[str] = "namespace.source_alias"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Wrong source for alias '{alias}': '{current_source}' -> '{correct_source}'"
    )

    def __init__(
        self,
        *,
        project_name: str,
        project_root: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize with project context and mandatory rope project."""
        super().__init__(rope_project=rope_project, parse_failures=parse_failures)
        self._project_name = project_name
        self._project_root = project_root

    @override
    def _collect_violations(
        self, file_path: Path
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        return self.detect_file(
            DetectorContext(
                file_path=file_path,
                project_name=self._project_name,
                project_root=self._project_root,
                rope_project=self._rope,
                parse_failures=self._pf,
            ),
        )

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: DetectorContext,
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        """Detect wrong-source alias imports."""
        file_path = ctx.file_path
        project_root = ctx.project_root
        if project_root is None:
            return []
        package_name = cls.discover_project_package_name(project_root=project_root)
        if not package_name:
            return []
        transformer = cls._get_transformer()
        if transformer is None:
            return []
        violations_raw = transformer.detect_file(
            file_path=file_path,
            project_package=package_name,
            alias_map=None,
        )
        return [
            m.Infra.NamespaceSourceViolation(
                file=getattr(raw, "file", ""),
                line=getattr(raw, "line", 0),
                alias=getattr(raw, "current_import", "").rsplit(" ", maxsplit=1)[-1]
                if " " in getattr(raw, "current_import", "")
                else "",
                current_source=getattr(raw, "current_import", "").split(" ")[1]
                if " " in getattr(raw, "current_import", "")
                else "",
                correct_source=package_name,
                current_import=getattr(raw, "current_import", ""),
                suggested_import=getattr(raw, "suggested_import", ""),
            )
            for raw in violations_raw
            if getattr(raw, "violation_type", "") == "wrong_source"
        ]

    @staticmethod
    def discover_project_package_name(*, project_root: Path) -> str:
        """Discover the package name for a project root."""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / c.Infra.Files.INIT_PY).is_file()
        ]
        return package_dirs[0].name if package_dirs else ""

    @staticmethod
    def _get_transformer() -> p.Infra.ImportNormalizerTransformerLike | None:
        mod = __import__(
            "flext_infra.transformers", fromlist=["ImportNormalizerTransformer"]
        )
        obj = getattr(mod, "ImportNormalizerTransformer", None)
        return obj if isinstance(obj, p.Infra.ImportNormalizerTransformerLike) else None


__all__ = ["FlextInfraNamespaceSourceDetector"]
