"""Detector for identifying deep imports that should use top-level aliases.

This module detects import statements using deep module paths that could be
replaced with shorter alias imports from the package's public API.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
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


class FlextInfraImportAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detector for deep import paths that should use top-level aliases.

    Identifies deep imports (e.g., `from package.submodule.impl import Class`)
    that could be simplified using top-level aliases (e.g., `from package import Class`).
    """

    _rule_id: ClassVar[str] = "namespace.import_alias"

    @classmethod
    def _discover_package(cls, file_path: Path) -> str:
        """Discover the package name for a file path.

        Args:
            file_path: Path to the Python file.

        Returns:
            The top-level package name, or empty string if not found.

        """
        src_dir_name = c.Infra.Paths.DEFAULT_SRC_DIR
        parts = file_path.resolve().parts
        try:
            src_index = parts.index(src_dir_name)
        except ValueError:
            return ""
        package_index = src_index + 1
        if package_index >= len(parts):
            return ""
        return parts[package_index]

    def __init__(
        self,
        *,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraImportAliasDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format an import alias violation message.

        Args:
            violation: The violation model with current_import and suggested_import.

        Returns:
            Human-readable message for the import alias violation.

        """
        fields = violation.model_dump()
        current_import = fields.get("current_import", "")
        suggested_import = fields.get("suggested_import", "")
        return f"Deep import '{current_import}' should use '{suggested_import}'"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect import alias violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of ImportAliasViolation objects found.

        """
        return type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ImportAliasViolation]:
        """Detect import alias violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of ImportAliasViolation objects found in the file.

        """
        return cls.scan_file_impl(
            file_path=file_path,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        _parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ImportAliasViolation]:
        """Scan a file for deep import paths that should use aliases.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of ImportAliasViolation for each deep import found.

        """
        _ = _parse_failures
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
        violations_raw = transformer_obj.detect_file(
            file_path=file_path,
            project_package=cls._discover_package(file_path),
            alias_map=None,
        )
        violations: MutableSequence[m.Infra.ImportAliasViolation] = []
        for raw in violations_raw:
            violation_type = getattr(raw, "violation_type", "")
            file_value = getattr(raw, "file", "")
            line_value = getattr(raw, "line", 0)
            current_import = getattr(raw, "current_import", "")
            suggested_import = getattr(raw, "suggested_import", "")
            if violation_type != "deep":
                continue
            if not isinstance(file_value, str):
                continue
            if not isinstance(line_value, int):
                continue
            if not isinstance(current_import, str):
                continue
            if not isinstance(suggested_import, str):
                continue
            violations.append(
                m.Infra.ImportAliasViolation.create(
                    file=file_value,
                    line=line_value,
                    current_import=current_import,
                    suggested_import=suggested_import,
                ),
            )
        return violations


__all__ = ["FlextInfraImportAliasDetector"]
