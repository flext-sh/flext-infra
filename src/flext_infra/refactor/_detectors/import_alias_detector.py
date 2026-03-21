"""Detector for identifying deep imports that should use top-level aliases.

This module detects import statements using deep module paths that could be
replaced with shorter alias imports from the package's public API.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Protocol, override, runtime_checkable

from flext_infra import c, p
from flext_infra.refactor._detectors.module_loader import DetectorScanResultBuilder
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)
from flext_infra.transformers.project_discovery import ProjectAliasDiscovery

if TYPE_CHECKING:
    from flext_infra import m


@runtime_checkable
class _ImportNormalizerTransformerLike(Protocol):
    """Protocol for import normalizer transformer compatibility checking."""

    @staticmethod
    def detect_file(
        *,
        file_path: Path,
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[object]:
        """Detect import violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            project_package: The project package name.
            alias_map: Optional mapping of packages to their public aliases.

        Returns:
            List of violation objects found.

        """
        ...


class ImportAliasDetector(p.Infra.Scanner):
    """Detector for deep import paths that should use top-level aliases.

    Identifies deep imports (e.g., `from package.submodule.impl import Class`)
    that could be simplified using top-level aliases (e.g., `from package import Class`).
    """

    _alias_cache: ClassVar[dict[str, tuple[str, ...]] | None] = None

    @classmethod
    def _get_alias_map(
        cls, workspace_root: Path | None = None
    ) -> dict[str, tuple[str, ...]]:
        """Get the cached mapping of packages to their public aliases.

        Args:
            workspace_root: Optional workspace root to discover aliases from.

        Returns:
            Dict mapping package names to tuples of public alias names.

        """
        if cls._alias_cache is not None:
            return cls._alias_cache
        root = workspace_root if workspace_root is not None else Path.cwd()
        cls._alias_cache = ProjectAliasDiscovery.discover_workspace_aliases(root)
        return cls._alias_cache

    @classmethod
    def _suggest_alias_import(cls, *, package: str, imported_names: list[str]) -> str:
        """Suggest an alias import statement for the given names.

        Args:
            package: The package name being imported from.
            imported_names: List of names being imported.

        Returns:
            Suggested import statement using available aliases.

        """
        alias_map = cls._get_alias_map()
        allowed = alias_map.get(package, ())
        allowed_set = set(allowed)
        unique_names = {name for name in imported_names if name in allowed_set}
        ordered_names = [name for name in allowed if name in unique_names]
        return f"from {package} import {', '.join(ordered_names)}"

    @staticmethod
    def parse_imported_names(import_clause: str) -> list[str]:
        """Parse imported names from an import clause string.

        Args:
            import_clause: The import clause (e.g., 'A, B as C, D').

        Returns:
            List of original names being imported.

        """
        no_comment = import_clause.split("#", maxsplit=1)[0].strip()
        normalized_clause = no_comment.replace("(", "").replace(")", "")
        names: list[str] = []
        for part in normalized_clause.split(","):
            token_text = part.strip()
            if len(token_text) == 0:
                continue
            if " as " in token_text:
                token_text = token_text.split(" as ", maxsplit=1)[0].strip()
            names.append(token_text)
        return names

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
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the ImportAliasDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for import alias violations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected alias violations.

        """
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return DetectorScanResultBuilder.build(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id="namespace.import_alias",
            violations=violations,
            message_builder=lambda violation: (
                f"Deep import '{violation.current_import}' should use "
                f"'{violation.suggested_import}'"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ImportAliasViolation]:
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
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ImportAliasViolation]:
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
        if not isinstance(transformer_obj, _ImportNormalizerTransformerLike):
            return []
        violations_raw = transformer_obj.detect_file(
            file_path=file_path,
            project_package=cls._discover_package(file_path),
            alias_map=None,
        )
        violations: list[nem.ImportAliasViolation] = []
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
                nem.ImportAliasViolation.create(
                    file=file_value,
                    line=line_value,
                    current_import=current_import,
                    suggested_import=suggested_import,
                ),
            )
        return violations
