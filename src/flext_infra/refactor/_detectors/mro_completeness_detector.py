"""Detector for facade classes missing local MRO composition bases.

This module detects namespace facade classes that are missing bases from their
corresponding family modules, which violates the namespace composition pattern.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
from libcst import metadata as cst_metadata

from flext_infra import (
    FlextInfraNamespaceEnforcerModels as nem,
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraMROCompletenessDetector(
    p.Infra.Scanner,
):
    """Detector for facade classes missing MRO composition bases.

    Identifies namespace facade classes that lack bases from their family modules,
    ensuring complete composition of constants, types, protocols, models, and utilities.
    """

    FAMILY_DIR_BY_ALIAS: ClassVar[t.StrMapping] = {
        "c": "_constants",
        "t": "_typings",
        "p": "_protocols",
        "m": "_models",
        "u": "_utilities",
    }

    def __init__(
        self,
        *,
        parse_failures: MutableSequence[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraMROCompletenessDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file for MRO completeness violations.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected MRO violations.

        """
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return u.Infra.build_scan_result(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id="namespace.mro_completeness",
            violations=violations,
            message_builder=lambda violation: (
                f"Facade '{violation.facade_class}' missing base "
                f"'{violation.missing_base}' for family '{violation.family}'"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: MutableSequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.MROCompletenessViolation]:
        """Detect MRO completeness violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of MROCompletenessViolation objects found in the file.

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
        _parse_failures: MutableSequence[nem.ParseFailureViolation] | None = None,
    ) -> Sequence[nem.MROCompletenessViolation]:
        """Scan a facade file for missing local composition bases.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Unused parameter for interface compatibility.

        Returns:
            List of MROCompletenessViolation for each missing base found.

        """
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        tree = cls._parse_module(
            file_path=file_path,
            stage="mro-completeness-scan",
            parse_failures=_parse_failures,
        )
        if tree is None:
            return []
        facade_name = cls._resolve_facade_class_name(tree=tree, family=family)
        if facade_name is None:
            return []
        facade_node = cls._find_top_level_class(
            tree=tree,
            class_name=facade_name,
        )
        if facade_node is None:
            return []
        declared_bases = {
            base_name
            for base_name in (
                cls._extract_base_name(base) for base in facade_node.bases
            )
            if base_name
        }
        candidates = cls._collect_local_candidates(
            file_path=file_path,
            facade_name=facade_name,
            family=family,
            _parse_failures=_parse_failures,
        )
        violations: MutableSequence[nem.MROCompletenessViolation] = []
        for candidate_name, candidate_line in sorted(
            candidates,
            key=operator.itemgetter(0),
        ):
            if candidate_name in declared_bases:
                continue
            violations.append(
                nem.MROCompletenessViolation.create(
                    file=str(file_path),
                    line=candidate_line,
                    family=family,
                    facade_class=facade_name,
                    missing_base=candidate_name,
                    suggestion=(
                        f"Add '{candidate_name}' to '{facade_name}' inheritance bases"
                    ),
                ),
            )
        return violations

    @staticmethod
    def _resolve_facade_class_name(*, tree: cst.Module, family: str) -> str | None:
        """Resolve the facade class name for a family.

        Args:
            tree: The CST module to analyze.
            family: The family identifier (e.g., 'c', 't', 'p', 'm', 'u').

        Returns:
            The facade class name, or None if not found.

        """
        for item in tree.body:
            if not isinstance(item, cst.SimpleStatementLine):
                continue
            for stmt in item.body:
                if not isinstance(stmt, cst.Assign):
                    continue
                if not isinstance(stmt.value, cst.Name):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target.target, cst.Name)
                        and target.target.value == family
                    ):
                        return stmt.value.value
        suffix = c.Infra.FAMILY_SUFFIXES.get(family, "")
        if not suffix:
            return None
        for stmt in tree.body:
            if isinstance(stmt, cst.ClassDef) and stmt.name.value.endswith(suffix):
                return stmt.name.value
        return None

    @staticmethod
    def _find_top_level_class(
        *,
        tree: cst.Module,
        class_name: str,
    ) -> cst.ClassDef | None:
        """Find a top-level class definition by name.

        Args:
            tree: The CST module to search.
            class_name: The name of the class to find.

        Returns:
            The ClassDef node if found, None otherwise.

        """
        for stmt in tree.body:
            if isinstance(stmt, cst.ClassDef) and stmt.name.value == class_name:
                return stmt
        return None

    @staticmethod
    def _extract_base_name(base: cst.Arg) -> str:
        """Extract the base class name from a class base argument.

        Args:
            base: A class base argument node.

        Returns:
            The base class name, or empty string if unable to extract.

        """
        value = base.value
        if isinstance(value, cst.Name):
            return value.value
        if isinstance(value, cst.Attribute):
            return u.Infra.cst_module_to_str(value)
        if isinstance(value, cst.Subscript):
            return FlextInfraMROCompletenessDetector._expr_to_base_name(value.value)
        return ""

    @staticmethod
    def _expr_to_base_name(value: cst.BaseExpression) -> str:
        """Convert an expression to a base class name.

        Args:
            value: An expression node to convert.

        Returns:
            The base class name, or empty string if unable to extract.

        """
        if isinstance(value, cst.Name):
            return value.value
        if isinstance(value, cst.Attribute):
            return u.Infra.cst_module_to_str(value)
        return ""

    @classmethod
    def _collect_local_candidates(
        cls,
        *,
        file_path: Path,
        facade_name: str,
        family: str,
        _parse_failures: MutableSequence[nem.ParseFailureViolation] | None,
    ) -> set[tuple[str, int]]:
        """Collect candidate base classes from the family module.

        Args:
            file_path: Path to the facade file.
            facade_name: Name of the facade class.
            family: The family identifier.
            _parse_failures: Optional list to track parse failures.

        Returns:
            Set of (class_name, line_number) tuples for candidate bases.

        """
        candidates: set[tuple[str, int]] = set()
        facade_prefix = facade_name
        candidates.update(
            cls._collect_from_module(
                file_path=file_path,
                facade_prefix=facade_prefix,
                facade_name=facade_name,
                _parse_failures=_parse_failures,
            ),
        )
        family_dir_name = cls.FAMILY_DIR_BY_ALIAS.get(family, "")
        if family_dir_name:
            family_dir = file_path.parent / family_dir_name
            if family_dir.is_dir():
                for child in sorted(family_dir.glob("*.py")):
                    candidates.update(
                        cls._collect_from_module(
                            file_path=child,
                            facade_prefix=facade_prefix,
                            facade_name=facade_name,
                            _parse_failures=_parse_failures,
                        ),
                    )
            family_file = file_path.parent / f"{family_dir_name}.py"
            if family_file.is_file():
                candidates.update(
                    cls._collect_from_module(
                        file_path=family_file,
                        facade_prefix=facade_prefix,
                        facade_name=facade_name,
                        _parse_failures=_parse_failures,
                    ),
                )
        return candidates

    @staticmethod
    def _collect_from_module(
        *,
        file_path: Path,
        facade_prefix: str,
        facade_name: str,
        _parse_failures: MutableSequence[nem.ParseFailureViolation] | None,
    ) -> set[tuple[str, int]]:
        tree = FlextInfraMROCompletenessDetector._parse_module(
            file_path=file_path,
            stage="mro-completeness-candidates",
            parse_failures=_parse_failures,
        )
        if tree is None:
            return set()
        wrapper = cst_metadata.MetadataWrapper(tree, unsafe_skip_copy=True)
        positions = wrapper.resolve(cst_metadata.PositionProvider)
        result: set[tuple[str, int]] = set()
        for stmt in tree.body:
            if not isinstance(stmt, cst.ClassDef):
                continue
            class_name = stmt.name.value
            if class_name == facade_name:
                continue
            if class_name.startswith("_"):
                continue
            if not class_name.startswith(facade_prefix):
                continue
            position = positions.get(stmt)
            line = position.start.line if position is not None else 0
            result.add((class_name, line))
        return result

    @staticmethod
    def _parse_module(
        *,
        file_path: Path,
        stage: str,
        parse_failures: MutableSequence[nem.ParseFailureViolation] | None,
    ) -> cst.Module | None:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            return cst.parse_module(source)
        except UnicodeDecodeError as exc:
            FlextInfraMROCompletenessDetector._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        except OSError as exc:
            FlextInfraMROCompletenessDetector._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        except cst.ParserSyntaxError as exc:
            FlextInfraMROCompletenessDetector._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type="SyntaxError",
                detail=str(exc),
            )
            return None

    @staticmethod
    def _append_parse_failure(
        *,
        parse_failures: MutableSequence[nem.ParseFailureViolation] | None,
        file_path: Path,
        stage: str,
        error_type: str,
        detail: str,
    ) -> None:
        if parse_failures is None:
            return
        parse_failures.append(
            nem.ParseFailureViolation.create(
                file=str(file_path),
                stage=stage,
                error_type=error_type,
                detail=detail,
            ),
        )
