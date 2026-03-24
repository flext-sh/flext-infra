"""Detector for identifying alias imports from wrong source packages.

This module detects imports that import public aliases from internal/wrong source
packages instead of the correct canonical source.
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import (
    c,
    m,
    p,
)

from ._base_detector import FlextInfraScanFileMixin


class FlextInfraNamespaceSourceDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for alias imports from wrong source packages.

    Identifies imports that source public aliases from internal or wrong packages
    instead of the canonical/correct source package.
    """

    _rule_id: ClassVar[str] = "namespace.source_alias"

    def __init__(
        self,
        *,
        project_name: str,
        project_root: Path,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraNamespaceSourceDetector scanner.

        Args:
            project_name: Name of the project being scanned.
            project_root: Root directory of the project.
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures
        self._project_name = project_name
        self._project_root = project_root

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format a namespace source violation message.

        Args:
            violation: The violation model with alias, current_source, correct_source.

        Returns:
            Human-readable message for the namespace source violation.

        """
        fields = violation.model_dump()
        alias = fields.get("alias", "")
        current_source = fields.get("current_source", "")
        correct_source = fields.get("correct_source", "")
        return (
            f"Wrong source for alias '{alias}': "
            f"'{current_source}' -> '{correct_source}'"
        )

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect namespace source violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of NamespaceSourceViolation objects found.

        """
        return type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            project_root=self._project_root,
            _parse_failures=self._parse_failures,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        project_name: str,
        project_root: Path,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        """Detect namespace source violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            project_name: Name of the project being scanned.
            project_root: Root directory of the project.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of NamespaceSourceViolation objects found in the file.

        """
        return cls.scan_file_impl(
            file_path=file_path,
            project_name=project_name,
            project_root=project_root,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        project_name: str,
        project_root: Path,
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.NamespaceSourceViolation]:
        """Scan a file for wrong-source alias imports."""
        _ = project_name
        _ = _parse_failures
        package_name = cls._discover_project_package_name(project_root=project_root)
        if not package_name:
            return []
        transformers_module = __import__(
            "flext_infra.transformers",
            fromlist=["ImportNormalizerTransformer"],
        )
        transformer_obj = getattr(
            transformers_module,
            "ImportNormalizerTransformer",
            None,
        )
        if not isinstance(transformer_obj, p.Infra.ImportNormalizerTransformerLike):
            return []
        violations_cst = transformer_obj.detect_file(
            file_path=file_path,
            project_package=package_name,
            alias_map=None,
        )
        violations: MutableSequence[m.Infra.NamespaceSourceViolation] = []
        for raw in violations_cst:
            violation_type = getattr(raw, "violation_type", "")
            file_value = getattr(raw, "file", "")
            line_value = getattr(raw, "line", 0)
            current_import = getattr(raw, "current_import", "")
            suggested_import = getattr(raw, "suggested_import", "")
            if violation_type != "wrong_source":
                continue
            if not isinstance(file_value, str):
                continue
            if not isinstance(line_value, int):
                continue
            if not isinstance(current_import, str):
                continue
            if not isinstance(suggested_import, str):
                continue
            alias = (
                current_import.rsplit(" ", maxsplit=1)[-1]
                if " " in current_import
                else ""
            )
            current_source = (
                current_import.split(" ")[1] if " " in current_import else ""
            )
            violations.append(
                m.Infra.NamespaceSourceViolation.create(
                    file=file_value,
                    line=line_value,
                    alias=alias,
                    current_source=current_source,
                    correct_source=package_name,
                    current_import=current_import,
                    suggested_import=suggested_import,
                ),
            )
        return violations

    @staticmethod
    def _discover_project_package_name(*, project_root: Path) -> str:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / "__init__.py").is_file()
        ]
        if not package_dirs:
            return ""
        return package_dirs[0].name

    @classmethod
    def discover_project_package_name(cls, *, project_root: Path) -> str:
        """Discover the package name for a project root."""
        return cls._discover_project_package_name(project_root=project_root)


__all__ = ["FlextInfraNamespaceSourceDetector"]
